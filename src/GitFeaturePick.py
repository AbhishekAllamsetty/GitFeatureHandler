from git import Repo, Commit
from datetime import datetime
import logging
import json
import sys
from os import path
import os
import shutil
import pathlib


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

    def checkout_tgt_branch(self):
        """

        :return:
        """
        tgt_branch = self.config_params['git_config']['target_branch']
        try:
            # trying to checkout as new branch first
            # in case it exists then we will checkout normally
            self.logger.info("Trying to checkout  '{}'  as new branch".format(tgt_branch))
            self.target_repo.git.checkout("-b", tgt_branch)

        except Exception as ex:
            # if exception is raised it means the branch is already available
            # so checking out locally
            self.logger.info("Target branch available. Checking out to  '{}'  locally".format(tgt_branch))
            self.target_repo.git.checkout(tgt_branch)

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
                        'existing_path': item.b_blob.path,
                        'new_path': item.a_path
                    }
                    self.config_params['file_types']['R'].append(tmp_dit)

        except Exception as ex:
            raise Exception("identify_changes()  ::  {}".format(ex))

    def get_abs_path(self, file):
        """
        this will conact the file path with base dir
        replace / -> \
        for destination path file name will be removed and will its parent dir
        Not returning target path as path object as it needs to go with some enhancements
        respective to removals of file name from path
        :param file: file along with repo path
        :return: base_dir + file_path + file_name/parent_dir
        """
        try:
            source_base_path = self.config_params['git_config']['base_repo_path']
            target_base_path = self.config_params['git_config']['target_repo_path']

            # appending file with source path
            src = source_base_path + "\\" + file.replace("/", "\\")

            # appending file with destination path and removing the last index (i.e file name)
            tgt = target_base_path + "\\" + file.replace("/", "\\")

            return self.get_path_obj(src), self.get_path_obj(tgt)

        except Exception as ex:
            raise Exception("get_abs_path()  :: {}".format(ex))

    def handle_modified_types(self):
        """
        here we force copy all the files from source branch to target branch
        :return: None
        """
        try:
            for file in self.config_params['file_types']['M']:
                # fetching the src and tgt paths from a file appending the base dir
                src, tgt = self.get_abs_path(file)

                # taking the parent directory of the target file and checking if its available
                # so that the file can be moved
                tgt = self.get_path_obj(os.path.dirname(tgt))

                # copying the file only if src and dst are available
                if path.exists(src) is True and path.exists(tgt) is True:
                    # self.logger.info("Copying {} -> {}".format(src, tgt))
                    shutil.copy(src, tgt)

        except Exception as ex:
            raise Exception("handle_modified_types()  ::  {}".format(ex))

    def handle_added_types(self):
        """
        here we copy all the newly added files
        :return: None
        """
        try:
            for file in self.config_params['file_types']['A']:
                # fetching the src and tgt paths from a file appending the base dir
                src, tgt = self.get_abs_path(file)

                # taking dir path so that the src file can move to tgt path
                tgt = self.get_path_obj(os.path.dirname(tgt))

                # self.logger.critical("{} -> {}".format(src, tgt))
                # checking dir and files available or not
                # copying the file only if src and dst are available
                if path.exists(src) is True:
                    # creating a target_dir only if src file exists
                    # else it would be unnecessary to create a dir
                    if path.exists(tgt) is False:
                        os.mkdir(tgt)

                    shutil.copy(src, tgt)

        except Exception as ex:
            raise Exception("handle_added_types()  ::  {}".format(ex))

    def handle_delete_types(self):
        """
        here we delete the files which need to be deleted in the commit
        Firstly we check if file which need to be deleted exists in destination location
        and if it exists then we delete the file
        :return: None
        """
        try:
            for file in self.config_params['file_types']['D']:
                # fetching the abs paths
                src, tgt = self.get_abs_path(file)

                # self.logger.info("{} -> {}".format(src, tgt))

                # checking dir and files available or not
                if path.exists(tgt) is True:
                    # checking if g is file or dir
                    if os.path.isfile(tgt):
                        os.remove(tgt)

                    elif os.path.isdir(tgt):
                        # this removes the dir forcefully even if files exists
                        shutil.rmtree(tgt)

        except Exception as ex:
            raise Exception("handle_delete_types  ::  {}".format(ex))

    def handle_renamed_types(self):
        """
        this function handles the renamed files and directories
        :return: None
        """
        try:
            for file in self.config_params['file_types']['R']:

                # checking if exising path which needs to be renamed
                # is available in target repo or not
                if file:
                    old_src, old_tgt = self.get_abs_path(file['existing_path'])
                    new_src, new_tgt = self.get_abs_path(file['new_path'])

                    # for debugging
                    # self.logger.info("{} -> {}".format(old_tgt, new_tgt))

                    # checking the file which needs to be renamed
                    # is available in target repo or not.
                    # checking if the path is available tgt repo location and renaming it
                    if os.path.exists(old_tgt) and os.path.exists(new_tgt) is False:
                        os.rename(old_tgt, new_tgt)

        except Exception as ex:
            raise Exception("handle_renamed_types()  ::  {}".format(ex))

    @staticmethod
    def get_path_obj(path):
        """
        this function returns a abs path object
        :param path: a string path
        :return: a path object
        """
        try:
            return pathlib.Path(path)

        except Exception as ex:
            raise Exception("get_path_obj()  ::  {}".format(ex))

    def main_method(self):
        """
        main method starts here
        :return: None
        """
        try:
            self.logger.info("Initializing the commits collection")

            # checkout to target branch
            self.checkout_tgt_branch()

            # getting unsorted commits
            self.get_unsorted_commits()

            for commit in sorted(self.commits_list, key=lambda x: datetime.strptime(x[1], "%d-%m-%Y %H:%M:%S:%f")):

                # re-initializing the file types for every commit
                # keeping it clean after file moments of every commit hash
                self.config_params['file_types'] = {'M':[], 'A': [], 'D': [], 'R': []}

                # identifying the change_types and collecting the items
                self.identify_changes(commit=commit[0])

                # adding new files
                self.logger.info("Adding new files for commit  ::  {}".format(commit))
                self.handle_added_types()

                # copy files function
                self.logger.info("Coping modified files for commit  ::  {}".format(commit))
                self.handle_modified_types()

                # removing files / dir
                self.logger.info("Removing files/dir for commit  ::  {}".format(commit))
                self.handle_delete_types()

                # rename file/ dir
                self.logger.info("Handling rename files/dir for commit  ::  {}".format(commit))
                self.handle_renamed_types()

            # adding the changes to repo
            self.logger.info("Adding all the changes")
            self.target_repo.git.add(u=True)

            # commiting and pushing the changes
            self.logger.info("Committing and pushing changes")
            self.target_repo.index.commit("Committing Changes")
            self.target_repo.git.push('origin', self.config_params['git_config']['target_branch'])
            # origin = self.target_repo.remote(name=)
            # origin.push()

            self.logger.info("Job Successful!!")

        except Exception as ex:
            raise Exception("main_method  ::  {}".format(ex))


if __name__ == '__main__':

    git = GitFeaturePick()
    git.main_method()
