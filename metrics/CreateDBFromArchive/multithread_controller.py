import argparse
import multiprocessing
import os
import time

import psycopg2

import worker


class Controller:
    def __init__(self, archive_path, words):
        self._archive_path = archive_path
        self._words = words

        self._task_size = 4

        self._n_files_done = multiprocessing.Value('i', 0)
        self._total_files = 0

        for _, _, files in os.walk(self._archive_path):
            for file in files:
                if file.endswith("bz2"):
                    self._total_files += 1

    def _worker(self, task_queue):
        DBworker = worker.Worker(self._words)
        while not task_queue.empty():
            crt_task = task_queue.get()
            DBworker.json_to_db(crt_task)

            with self._n_files_done.get_lock():
                self._n_files_done.value += self._task_size
                if self._n_files_done.value < self._total_files:
                    print("Files done: " + str(self._n_files_done.value) +
                          " out of " + str(self._total_files),
                          end='\r')
                else:
                    print("Files done: " + str(self._n_files_done.value) +
                          " out of " + str(self._total_files),
                          end='\n')

    def _populate_tasks(self, task_queue):
        all_files = []
        for root, dirs, files in os.walk(self._archive_path):
            for file in files:
                if file.endswith("bz2"):
                    all_files.append(os.path.join(root, file))

        for idx in range(0, len(all_files), self._task_size):
            task_queue.put(all_files[idx:idx + self._task_size])

        return task_queue

    @staticmethod
    def _setup_database():
        try:
            # Establish connection
            connection = psycopg2.connect(user="postgres",
                                          password="pass123",
                                          host="127.0.0.1",
                                          port="5432",
                                          database="postgres")

            # Create tweets table
            drop_first = '''DROP TABLE IF EXISTS tweets'''
            cursor = connection.cursor()
            cursor.execute(drop_first)

            create_table_query = ''' CREATE TABLE tweets
                                     (ID SERIAL PRIMARY KEY,
                                      created_at TIMESTAMP NOT NULL,
                                      text TEXT NOT NULL,
                                      usr VARCHAR (255) NOT NULL,
                                      twid VARCHAR (255) NOT NULL,
                                      rt_status BOOLEAN NOT NULL);
                                 '''
            cursor.execute(create_table_query)
        except psycopg2.Error as error:
            print("Error while connecting to PostgreSQL", error)
        finally:
            # Batch commit all changes
            connection.commit()

            # Close connection
            if connection:
                cursor.close()
                connection.close()

    def run(self):
        self._setup_database()

        empty_task_queue = multiprocessing.Queue()
        full_task_queue = self._populate_tasks(empty_task_queue)
        processes = []
        n_processes = multiprocessing.cpu_count()
        print(f'Running with {n_processes} processes!')
        start = time.time()
        for w in range(n_processes):
            p = multiprocessing.Process(
                target=self._worker, args=(full_task_queue,))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        print(f'Time taken = {time.time() - start:.10f}')
        for p in processes:
            p.close()


def main():
    parser = argparse.ArgumentParser(description='Create DB from tweets')
    parser.add_argument('-a', help='Path to the archive')
    parser.add_argument('words', metavar='W', type=str, nargs='+', help='Words used for filtering')

    args = parser.parse_args()
    path = args.a
    words = args.words

    runner = Controller(path, words)

    print("Started job")

    runner.run()

    print("\nFinished job")


if __name__ == "__main__":
    main()

