from snow_ipa.services.gee.exports import ExportList
from snow_ipa.utils import dates
from typing import Any
from colorama import Fore, Style


class ExportManager:
    """
    A class to manage export operations.
    """

    # Upstream asset lists
    modis_status: dict[str, Any]
    modis_distinct_months: list[str]

    def __init__(
        self,
        export_to_gee: bool = False,
        export_to_gdrive: bool = False,
        gee_asset_path: str = "",
        gdrive_asset_path: str = "",
        months_to_save: list = [],
        image_prefix: str = "",
    ) -> None:

        # General Export Plan - If no explicit request, save last month
        self.image_prefix: str = image_prefix
        self.export_plan: dict = {"planned": [], "excluded": {}}
        self.export_tasks = ExportList()

        if not months_to_save:
            prev_month = dates.prev_month_last_date().strftime("%Y-%m-01")
            months_to_save = [prev_month]
        self.export_plan["planned"] = months_to_save

        # GEE Export Plan
        self.export_to_gee: bool = export_to_gee
        self.gee_assets_path: str = gee_asset_path
        self.gee_saved_assets: list[str] = []
        self.gee_saved_assets_months: list[str] = []
        self.gee_assets_to_save: list[str] = []

        # GDrive Export Plan
        self.export_to_gdrive: bool = export_to_gdrive
        self.gdrive_assets_path: str = gdrive_asset_path
        self.gdrive_saved_assets: list[str] = []
        self.gdrive_saved_assets_months: list[str] = []
        self.gdrive_assets_to_save: list[str] = []

        # Exclusion details. Can include duplicates if the image is being saved to both GEE and GDrive
        self.assets_excluded: dict = {}  #! No longer used

    # ! Method/Property might no longer be needed
    @property
    def final_assets_to_save(self) -> list:
        """
        Returns the final assets to save based on the export options.

        Returns:
            list: The final assets to save.
        """

        final_export_list = list(
            set(self.gee_assets_to_save + self.gdrive_assets_to_save)
        )
        final_export_list.sort()
        return final_export_list  # ! Method/Property might no longer be needed

    def print_export_plan(self) -> str:
        """
        Returns the export plan as a string.

        Returns:
            str: The export plan.
        """
        if not self.export_plan:
            return "No export plan available."

        str_export_plan = "EXPORT PLAN:\n"
        str_export_plan += f"{Fore.GREEN}To Export:{Style.RESET_ALL}\n"
        if self.export_plan["final_plan"]:
            str_export_plan += "\n".join(
                [f"  |- {month}" for month in self.export_plan["final_plan"]]
            )
        else:
            str_export_plan += "- No images to export"

        if list(self.export_plan["excluded"].keys()):
            str_export_plan += f"\n{Fore.GREEN}Excluded:{Style.RESET_ALL}\n"
            str_excluded = [
                f"  |- {key}: {value}"
                for key, value in self.export_plan["excluded"].items()
            ]
            str_export_plan += "\n".join(str_excluded)

        return str_export_plan

    def print_export_status(self) -> str:
        """
        Returns a string representing the status of an export tasks in export_tasks.
        Returns:
            str: The export status.
        """
        str_export_status = "EXPORT STATUS:\n"
        if not self.export_tasks.export_tasks:
            str_export_status += "No export tasks available."
            return str_export_status

        # Convert list of tasks to a string representation
        task_str = [
            {
                "str": f"  |- {task.image}: {task.status}{f' - {task.error}' if task.error else ''}",
                "target": task.target,
            }
            for task in self.export_tasks.export_tasks
        ]

        if self.export_to_gee:
            str_export_status += f"{Fore.GREEN}GEE Exports:{Style.RESET_ALL} \n"
            gee_tasks = [task["str"] for task in task_str if task["target"] == "gee"]
            str_export_status += "\n".join(gee_tasks)

        if self.export_to_gdrive and self.export_to_gee:
            str_export_status += f"\n"

        if self.export_to_gdrive:
            str_export_status += (
                f"{Fore.GREEN}Google Drive Exports:{Style.RESET_ALL} \n"
            )
            gdrive_tasks = [
                task["str"] for task in task_str if task["target"] == "gdrive"
            ]
            str_export_status += "\n".join(gdrive_tasks)

        return str_export_status
