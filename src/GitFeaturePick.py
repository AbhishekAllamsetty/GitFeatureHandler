from git import Repo, Commit
from datetime import datetime
import logging
import json
import sys
import os


class GitFeaturePick:

    def __init__(self):

        # Creating logging object
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format="%(asctime)s: [%(levelname)s]: %(name)s: %(message)s")

        # commits list
        self.commits_list = []

        # json props and repo obj
        self.config_params = json.loads(open(sys.argv[1]).read())
        self.base_repo = Repo(self.config_params['git_config']['base_repo_path'])
        self.target_repo = Repo(self.config_params['git_config']['target_repo_path'])

    def get_unsorted_commits(self):
        """
        This function is used to get the list of unsorted list commits
        for each and every jira ID and fetches the commits and its respective timestamp in a
        commit_list = [ [id, ts], [id, ts],...]
        :return: unsorted list of commit ids
        """
        try:
            # lopping in for every jira id over every commit log and capturing its commit hash and respective date
            # once the
            for jira_id in self.config_params['git_config']['expected_jira_id_list']:
                self.logger.info("Fetching commits for Jira ID  ::  {}".format(jira_id))

                # looping in for each and every commits by restricting them to jira_id value in commit message
                # and capturing those respective commit hash
                for commit in self.base_repo.iter_commits():
                    if commit.message.__contains__(jira_id):

                        # creating a list with commit_hash and datetime and appending to commit_list
                        tmp_lst = [commit, commit.committed_datetime.strftime("%d-%m-%Y %H:%M:%S:%f")]
                        self.commits_list.append(tmp_lst)

                self.logger.info("Completed fetching commits!")

        except Exception as ex:
            raise Exception("get_unsorted_commits()  ::  {}".format(ex))

    def identify_changes(self, commit):
        """
        Here we iterate for every file available in the respective commit and identify the change type

        if change type is M:
            file_path will be added to M list
        elif change type is A:
            file_path will be added to A list
        elif change type is D:
            file_path will be added to D list
        elif change type is R:
            previous_name and changed_name will be added to a dit = {}

        :param commit: commit hash
        :return: None
        """
        try:
            # looping in for each and every file and finding the change type
            for item in self.base_repo.index.diff(commit):
                if str(item.change_type) == 'A':
                    self.config_params['file_types']['A'].append(item.a_path)

                elif str(item.change_type) == 'M':
                    self.config_params['file_types']['M'].append(item.a_path)

                elif str(item.change_type) == 'D':
                    self.config_params['file_types']['D'].append(item.a_path)

                elif str(item.change_type) == 'R':
                    # in case of file re-write we need to rewrite file name
                    # so taking old name and new name
                    tmp_dit = {
                        'old_path': item.b_blob.path,
                        'new_path': item.a_path
                    }
                    self.config_params['file_types']['R'].append(tmp_dit)

        except Exception as ex:
            raise Exception("identify_changes()  ::  {}".format(ex))

    def handle_modified_types(self):
        """
        here we force copy all the files from source branch to target branch
        :return: None
        """
        try:
            source_base_path = self.config_params['git_config']['base_repo_path']
            target_base_path = self.config_params['git_config']['target_repo_path']

            for file in self.config_params['file_types']['M']:
                # appending file with source path
                src = source_base_path + "\\" + file.replace("/", "\\")

                # appending file with destination path and removing the last index (i.e file name)
                tgt = target_base_path + "\\" + file.replace("/", "\\")
                tgt = tgt.split("\\")[:-1]

                cmd = "copy /y {} {}".format(src, "\\".join(tgt))
                os.system(cmd)

        except Exception as ex:
            raise Exception("handle_modified_types()  ::  {}".format(ex))

    def main_method(self):
        """
        main method starts here
        :return: None
        """
        try:
            # getting unsorted commits
            self.get_unsorted_commits()

            for commit in sorted(self.commits_list, key=lambda x: datetime.strptime(x[1], "%d-%m-%Y %H:%M:%S:%f")):

                # re-initializing the file types for every commit
                # keeping it clean after file moments of every commit hash
                self.config_params['file_types'] = {'M':[], 'A': [], 'D': [], 'R': []}

                # identifying the change_types and collecting the items
                self.identify_changes(commit=commit[0])

                # copy files function
                self.logger.info("Coping modified files for commit  ::  {}".format(commit))
                self.handle_modified_types()

        except Exception as ex:
            raise Exception("main_method  ::  {}".format(ex))


if __name__ == '__main__':

    git = GitFeaturePick()
    git.main_method()

