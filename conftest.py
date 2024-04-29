import datetime
import os


def pytest_configure(config):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    report_directory = 'reports'
    report_filename = f'report_{timestamp}.html'

    if not os.path.exists(report_directory):
        os.makedirs(report_directory)

    full_report_path = os.path.join(config.rootdir, report_directory, report_filename)

    config.option.htmlpath = full_report_path
    config.option.self_contained_html = True


