import json

from string import Template


def generate_report(data: list, report_template: str, report_filename: str, report_size: int = None) -> bool:
    """Writes report of statistic data to file."""
    if report_size is None:
        report_size = len(data)
    if report_size < len(data):
        selected = sorted(data, key=lambda x: x['time_sum'], reverse=True)
        data = selected[:report_size]

    # converts floats to string for better view in report
    for d in data:
        d['time_med'] = "%.3f" % (d['time_med'])
        d['time_perc'] = "%.3f" % (d['time_perc'])
        d['time_avg'] = "%.3f" % (d['time_avg'])
        d['count_perc'] = "%.3f" % (d['count_perc'])
        d['time_sum'] = "%.3f" % (d['time_sum'])

    json_data = json.dumps(data)

    with open(report_template, mode='r', encoding='utf-8') as tf:
        template = Template(tf.read())

    with open(report_filename, mode='w', encoding='utf-8') as rf:
        rf.write(template.safe_substitute(table_json=json_data))

    return True
