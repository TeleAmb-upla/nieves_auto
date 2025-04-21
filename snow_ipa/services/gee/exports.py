import ee
import logging
import copy
import prettytable
from time import sleep


logger = logging.getLogger(__name__)


GEE_TASK_STATUS = {
    "COMPLETED": ["COMPLETED", "CANCELLED"],
    "FAILED": ["FAILED", "FAILED_TO_CREATE", "FAILED_TO_START"],
    "EXCLUDED": ["EXCLUDED", "MOCK_CREATED", "MOCK_TASK_SKIPPED", "ALREADY_EXISTS"],
    "PENDING": ["CREATED", "SUBMITTED", "STARTED", "RUNNING", "READY", "PENDING"],
    "UNKNOWN": ["FAILED_TO_GET_STATUS", "UNKNOWN"],
    "OTHER": ["PLANNED", "UNSUBMITTED", "NO_TASK_CREATED"],
}

GEE_TASK_VALID_STATUS = [
    status for statuses in GEE_TASK_STATUS.values() for status in statuses
]
GEE_TASK_SKIP_STATUS = [
    s
    for k, statuses in GEE_TASK_STATUS.items()
    if k in ["COMPLETED", "FAILED", "EXCLUDED", "OTHER"]
    for s in statuses
]
GEE_TASK_UNFINISHED_STATUS = [GEE_TASK_STATUS["PENDING"], GEE_TASK_STATUS["UNKNOWN"]]
GEE_TASK_FINISHED_STATUS = [GEE_TASK_STATUS["COMPLETED"], GEE_TASK_STATUS["FAILED"]]

GEE_EXPORT_VALID_STATUS = [status for status in GEE_TASK_STATUS.keys()]
MAX_STATUS_UPDATE_FAILURES = 3


class ExportTask:
    task: ee.batch.Task | None
    image: str
    date: str
    _target: str
    _status: str
    _export_status: str
    error: str | None
    status_update_failures: int = 0

    def __init__(
        self,
        image: str,
        date: str,
        target: str,
        status: str,
        task: ee.batch.Task | None = None,
    ) -> None:
        self.task = task
        self.image = image
        self.date = date
        self.target = target
        self.status = status
        self.error = None

    @property
    def target(self) -> str:
        return self._target

    @target.setter
    def target(self, value) -> None:
        value = value.upper()
        if value not in ["gee", "gdrive"]:
            raise ValueError(f"Can't create ExportTask, invalid target: {value}.")
        self._target = value

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value) -> None:
        value = value.upper()
        if value not in GEE_TASK_VALID_STATUS:
            raise ValueError(f"Invalid task status: {value}.")
        self._status = value
        self.export_status = value

    @property
    def export_status(self) -> str:
        return self._export_status

    @export_status.setter
    def export_status(self, value) -> None:
        value = value.upper()
        export_status = None
        for key, statuses in GEE_TASK_STATUS.items():
            if value in statuses:
                export_status = key
                break

        if export_status is None:
            export_status = "OTHER"

        self._export_status = export_status

    def start_task(self) -> str:
        """
        Start the export task.
        """
        if self.task is None:
            return "NO_TASK_CREATED"

        try:
            self.task.start()
            self.status = "STARTED"
        except Exception as e:
            self.status = "FAILED_TO_START"
            self.error = str(e)
            logger.error(f"Failed to start task: {self.image} to {self.target}")
            logger.error(e)
        return self.status

    def query_status(self) -> str:
        if self.task is None:
            return "NO_TASK_CREATED"

        if self.status_update_failures >= MAX_STATUS_UPDATE_FAILURES:
            logger.error(f"Task {self.image} to {self.target} failed to get status.")
            self.status = "FAILED_TO_GET_STATUS"
            return self.status

        try:
            status = self.task.status()
            status = status["state"]
            self.status_update_failures = 0
            self.error = None
            self.status = status
        except Exception as e:
            self.status_update_failures += 1
            self.error = str(e)
            logger.error(e)
        finally:
            return self.status


class ExportList:
    """
    A class to manage a list of export tasks.
    """

    export_tasks: list[ExportTask] = []

    def __init__(self, export_tasks: list[ExportTask] = []) -> None:
        if export_tasks:
            if any(not isinstance(task, ExportTask) for task in export_tasks):
                raise TypeError("export_tasks must be a list of ExportTask objects")
            self.export_tasks = copy.deepcopy(export_tasks)

    def add_task(self, task: ExportTask) -> None:
        """
        Add a task to the export tasks list.

        Args:
            task (ExportTask): The export task to add.
        """
        self.export_tasks.append(task)

    def export_summary(self, filter: str | None = None) -> dict[str, int]:

        filter_target = ["gee", "gdrive"]
        if filter is None:
            _filter = filter_target
        elif filter in filter_target:
            _filter = [filter]
        else:
            raise ValueError(
                f"Invalid filter: {filter}. Must be one of {filter_target}."
            )

        status_list = [
            t.export_status for t in self.export_tasks if t.target in _filter
        ]

        status_dict = {}
        for status in status_list:
            status_dict["status"] = len([s for s in status_list if s == status])

        return status_dict

    def pretty_export_summary(self, filter: str | None = None) -> str:
        status_dict = self.export_summary(filter=filter)
        table = prettytable.PrettyTable()
        table.field_names = [status_dict.keys()]
        table.add_row([status_dict.values()])
        return table.get_string()

    def track_exports(self, sleep_time: int = 60):
        """
        Start and track export tasks in the export_tasks list.

        Process will skip all tasks that are not dictionaries or do not have the required keys.
        required keys: ["task", "image", "target"]

        Args:
            sleep_time (int): Time in seconds to sleep between checking task status.

        Returns:
            dict: Summary of export tasks with their statuses.

        raises:
            TypeError: If export_tasks is not a list of ExportTask objects.
        """

        logger.debug("Starting export tasks...")

        ####### TRACK TASKS #######
        skipped_tasks = 0
        for i, task in enumerate(self.export_tasks):

            # Start task. Skip with "bad" status or mock tasks
            current_status = task.status
            if current_status in "CREATED":
                task.start_task()
                task.status = "STARTED"
            if current_status == "MOCK_CREATED":
                skipped_tasks += 1
                task.status = "MOCK_TASK_SKIPPED"
            else:
                skipped_tasks += 1
                logger.info(f"Skipping task: {task.image} with status {current_status}")

        logger.info(
            f"Started {len(self.export_tasks) - skipped_tasks} export tasks. Skipped {skipped_tasks} tasks."
        )

        ####### TRACK TASKS #######
        logger.debug("Tracking export tasks...")
        finished_tasks = []
        continue_tracking = True
        while continue_tracking:
            continue_tracking = False
            for i, task in enumerate(self.export_tasks):
                # Skip previously "finished" tasks to avoid logging multiple times
                if i not in finished_tasks:
                    if task.status in GEE_TASK_SKIP_STATUS:
                        finished_tasks.append(i)
                        continue

                    status = task.query_status()
                    if status in GEE_TASK_UNFINISHED_STATUS:
                        continue_tracking = True
                        continue

                    elif status in GEE_TASK_FINISHED_STATUS:
                        logger.info(
                            f"Task {task.image} to {task.target} finished with status: {status}"
                        )
                        finished_tasks.append(i)
                    else:
                        logger.warning(
                            f"Task {task.image} to {task.target} finished with unknown status: {status}"
                        )
                        finished_tasks.append(i)

            if continue_tracking:
                sleep(sleep_time)

        return self.export_summary()
