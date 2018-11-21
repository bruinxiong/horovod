# Copyright 2018 Uber Technologies, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import os
import sys
import threading
import time

from horovod.spark import codec, driver_service, task_service, secret


def parent_process_monitor(initial_ppid):
    while True:
        if initial_ppid != os.getppid():
            # Parent process died, terminate
            os._exit(1)
        time.sleep(1)


def main(driver_addresses):
    # Die if parent process terminates
    bg = threading.Thread(target=parent_process_monitor, args=(os.getppid(),))
    bg.daemon = True
    bg.start()

    key = codec.loads_base64(os.environ[secret.HOROVOD_SECRET_KEY])
    rank = int(os.environ['OMPI_COMM_WORLD_RANK'])
    driver_client = driver_service.DriverClient(driver_addresses, key)
    task_index = driver_client.task_index_by_rank(rank)
    task_addresses = driver_client.all_task_addresses(task_index)
    task_client = task_service.TaskClient(task_index, task_addresses, key)
    fn, args, kwargs = driver_client.code()
    result = fn(*args, **kwargs)
    task_client.register_code_result(result)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: %s <driver addresses>' % sys.argv[0])
        sys.exit(1)
    main(codec.loads_base64(sys.argv[1]))
