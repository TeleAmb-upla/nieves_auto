from ee import batch as ee_batch
import logging
import copy
import prettytable
from time import sleep


logger = logging.getLogger(__name__)

# TODO: Add __iter__ method to ExportList to iterate over tasks

GEE_TASK_STATUS = {
    "EXCLUDED": ["EXCLUDED", "MOCK_CREATED", "MOCK_TASK_SKIPPED", "ALREADY_EXISTS"],
    "NOT_STARTED": ["PLANNED", "CREATED", "UNSUBMITTED"],
    "PENDING": ["SUBMITTED", "PENDING", "STARTED", "READY", "RUNNING"],
    "COMPLETED": ["COMPLETED", "FINISHED", "CANCELLED"],
    "FAILED": ["FAILED", "FAILED_TO_CREATE", "FAILED_TO_START"],
    "UNKNOWN": ["FAILED_TO_GET_STATUS", "UNKNOWN"],
    "OTHER": ["NO_TASK_CREATED"],
}

GEE_TASK_VALID_STATUS = [
    status for statuses in GEE_TASK_STATUS.values() for status in statuses
]

# Shortcuts for groups of statuses
GEE_TASK_SKIP_STATUS = [
    s
    for k, statuses in GEE_TASK_STATUS.items()
    if k in ["EXCLUDED", "COMPLETED", "FAILED", "UNKNOWN", "OTHER"]
    for s in statuses
]

GEE_TASK_UNFINISHED_STATUS = GEE_TASK_STATUS["PENDING"]
GEE_TASK_FINISHED_STATUS = GEE_TASK_STATUS["COMPLETED"] + GEE_TASK_STATUS["FAILED"]

GEE_EXPORT_VALID_STATUS = [status for status in GEE_TASK_STATUS.keys()]
MAX_STATUS_UPDATE_FAILURES = 3


class ExportTask:
    # TODO: Add a default init status
    _target: str
    _status: str
    _export_status: str
    _status_update_failures: int = 0

    def __init__(
        self,
        image: str,
        date: str,
        target: str,
        status: str,
        task: ee_batch.Task | None = None,
    ) -> None:
        self.task: ee_batch.Task | None = task
        self.image: str = image
        self.date: str = date
        self.target = target
        self.status = status
        self.error: str | None = None

    @property
    def target(self) -> str:
        return self._target

    @target.setter
    def target(self, value: str) -> None:
        value = value.lower()
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
    def export_status(self, value: str) -> None:
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
            logger.warning(f"Task {self.image} to {self.target} is None.")
            if not self.status or self.status in GEE_TASK_STATUS["NOT_STARTED"]:
                self.status = "NO_TASK_CREATED"
            return self.status

        try:
            if self.status in GEE_TASK_STATUS["NOT_STARTED"]:
                self.task.start()
                self.status = "STARTED"
        except Exception as e:
            self.status = "FAILED_TO_START"
            self.error = str(e)
            logger.error(f"Failed to start task: {self.image} to {self.target}")
            logger.error(e)
        return self.status

    def query_status(self) -> str:

        # Skip if no task to track
        if self.task is None:
            if not self.status:
                self.status = "NO_TASK_CREATED"
            return self.status

        # if multiple status check fail, change status and stop checking
        if (
            self._status_update_failures >= MAX_STATUS_UPDATE_FAILURES
            and self.status != "FAILED_TO_GET_STATUS"
        ):
            logger.error(f"Task {self.image} to {self.target} failed to get status.")
            self.status = "FAILED_TO_GET_STATUS"
            return self.status

        try:
            if (
                self.status
                in GEE_TASK_STATUS["PENDING"] + GEE_TASK_STATUS["NOT_STARTED"]
            ):
                status = self.task.status()
                self.status = status["state"]
                self._status_update_failures = 0
                self.error = None

        except Exception as e:
            self._status_update_failures += 1
            self.error = str(e)
            logger.error(e)
        finally:
            return self.status

    def __repr__(self) -> str:
        return f"ExportTask(image={self.image}, target={self.target}, status={self.status})"

    def __str__(self) -> str:
        return f"(image={self.image}, target={self.target}, status={self.status})"


class ExportList:
    """
    A class to manage a list of export tasks.
    """

    def __init__(self, export_tasks: list[ExportTask] = []) -> None:
        self.export_tasks: list[ExportTask] = []
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
        """Count the number of tasks in each status.
        Args:
            filter (str): Filter the tasks by target. Can be "gee" or "gdrive".
                If None, all tasks are included.

        returns:
            dict: A dictionary with the count of tasks in each status.
        """
        filter = filter.lower() if filter else None
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

        status_dict: dict[str, int] = {}
        for status in set(status_list):
            status_dict[status] = len([s for s in status_list if s == status])

        return status_dict

    def pretty_export_summary(self, filter: str | None = None) -> str:
        """Count the number of tasks in each status and returns values in a pretty table.

        Args:
            filter (str): Filter the tasks by target. Can be "gee" or "gdrive".
                If None, all tasks are included.

        Returns:
            str: A string representation of the pretty table.
        """

        status_dict = self.export_summary(filter=filter)

        if not list(status_dict.keys()):
            return "No Export tasks"

        table = prettytable.PrettyTable()
        table.field_names = list(status_dict.keys())
        table.add_row(list(status_dict.values()))
        return table.get_string()

    def start_exports(self) -> dict[str, int]:
        """
        Start all export tasks.

        Process will skip all tasks that are not dictionaries or do not have the required keys.
        required keys: ["task", "image", "target"]

        Returns:
            dict: Summary of export tasks with their statuses.
        """
        logger.debug("Starting export tasks...")

        ####### START TASKS #######
        skipped_tasks = 0
        for i, task in enumerate(self.export_tasks):

            # Skip tasks with "bad" status or mock tasks
            current_status = task.status
            if current_status in GEE_TASK_STATUS["NOT_STARTED"]:
                task.start_task()
            else:
                skipped_tasks += 1
                logger.info(
                    f"Skipping task: {task.target} - {task.image} with status {current_status}"
                )

        logger.info(
            f"Started {len(self.export_tasks) - skipped_tasks} export tasks. Skipped {skipped_tasks} tasks."
        )
        return self.export_summary()

    def track_exports(self, sleep_time: int = 60) -> dict[str, int]:
        """
        Track export tasks querying status at specified time intervals.

        Args:
            sleep_time (int): Time in seconds to sleep between checking task status.

        Returns:
            dict: Summary of export tasks with their statuses.

        raises:
            TypeError: If export_tasks is not a list of ExportTask objects.
        """

        logger.debug("Tracking export tasks...")

        finished_tasks = []
        continue_tracking = True
        while continue_tracking:
            continue_tracking = False
            for i, task in enumerate(self.export_tasks):
                # Skip previously "finished" tasks to avoid logging multiple times
                if i not in finished_tasks:
                    if task.status not in GEE_TASK_UNFINISHED_STATUS:
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

    def __str__(self) -> str:

        summary = "\n".join([str(task) for task in self.export_tasks])
        return f"{summary}"

    def __repr__(self) -> str:
        return f"ExportList(export_tasks={self.export_tasks})"
