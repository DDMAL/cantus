import time
import requests

from django.core.management.base import BaseCommand, make_option
from django.conf import settings


class Command(BaseCommand):
    help = 'Poll Solr until the server is running'

    args = ""

    option_list = BaseCommand.option_list + (
        make_option('--timeout',
                    nargs=1,
                    type=int,
                    default=10 * 60,
                    help='Timeout for the command in seconds (0 to disable)'),

        make_option('--wait-between-polls',
                    nargs=1,
                    type=int,
                    default=3,
                    help='Time to wait between polls in seconds'),
    )

    def handle(self, *args, **kwargs):
        status_url = '{}/admin/ping?wt=json'.format(settings.SOLR_SERVER)

        self.stderr.write(status_url)

        poll_wait = kwargs['wait_between_polls']
        timeout = kwargs['timeout']

        last_state = None
        last_http_status = None

        self.stderr.write('Waiting for Solr...')

        start_time = time.time()

        while True:
            req_start = time.time()

            try:
                response = requests.get(status_url)
            except requests.ConnectionError:
                if last_state != 'failed':
                    self.stderr.write('Connection failed...')
                    self.stderr.write(response.content)
                    last_state = 'failed'
            else:
                if last_state != 'connected' or last_http_status != response.status_code:
                    self.stderr.write('Received response, status {}'.format(response.status_code))

                    last_state = 'connected'
                    last_http_status = response.status_code

                if response.status_code == 200:
                    try:
                        solr_status = response.json()['responseHeader']['status']

                        if solr_status == 0:
                            return

                        raise ValueError('Bad Solr response status: {}'.format(solr_status))
                    except (ValueError, TypeError, IndexError) as e:
                        if last_state != 'error':
                            self.stderr.write('Error reading content: {}'.format(e))
                            last_state = 'error'

            req_end = time.time()

            if timeout > 0 and req_end - start_time > timeout:
                raise ValueError('timeout exceeded')

            time.sleep(poll_wait - (req_end - req_start))
