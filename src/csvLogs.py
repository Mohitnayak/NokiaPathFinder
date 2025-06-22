from datetime import datetime

from basePath import get_base_path_for_time_range


class CSVLog:
    average_speed = 0
    average_distance_from_route = 0
    task_completion_time_s = 0
    deviation_zone_radius = 0


def get_csv_logs_for_time_range(
    db_path: str, time_range: tuple[datetime, datetime]
) -> CSVLog:
    base_path = get_base_path_for_time_range(db_path, time_range)
    csvLog = CSVLog()
    csvLog.deviation_zone_radius = base_path.deviation_zone_radius
    csvLog.task_completion_time_s = (time_range[1] - time_range[0]).total_seconds()

    return csvLog
