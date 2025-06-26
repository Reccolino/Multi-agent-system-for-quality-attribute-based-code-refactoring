import os
import time
from abc import ABC, abstractmethod
from git import Repo
import requests

from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.costants import header_git, DIRECTORY_REPOS, \
    APACHE_PATH, LPO_PATH
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.sonar_methods import create_project, \
     returns_metrics_pre_kickoff, returns_metrics_post_kickoff
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.utility_methods import final_report_excel


class BaseValidation(ABC):

   @abstractmethod
   def clone_apache_projects(self):
       pass

   @abstractmethod
   def clone_lpo_projects(self):
       pass

   # I keep the clones separate because they have slightly different logic when reading the JSON
   # (even though it would have been possible to create a single method and check the directory with an if,
   # this approach was preferred)

   @abstractmethod
   def creation_sonar_projects(self, directory):
       """
        Creates the local projects on SonarQube.
        Args:
            directory: directory containing all the projects saved locally
        """

       pass

   @abstractmethod
   def results_pre_refactoring(self, directory):
       """
        Displays the results of the static analysis performed by SonarQube for each project.
        Project cleanup: removal of projects that are not meaningful for the approach.

        Return:
            DataFrame with the pre-refactoring results
        """

       pass

   @abstractmethod
   def results_post_refactoring(self, directory):
       """
       Displays the results of the static analysis performed by SonarQube for each project, after the MAS refactoring.

       Return:
           - Dataframe with the post-refactoring results
           - Excel of pre and post datafraes
       """
       pass




class Validation(BaseValidation):



    def clone_apache_projects(self):

        repos_url= "https://api.github.com/search/repositories?q=apache+commons+language:java&per_page=17"

        response = requests.get(repos_url, headers=header_git)
        repos = response.json()

        for repository in repos["items"]:
            clone_url = repository.get("clone_url")
            print(f"Cloning {clone_url}")
            path_destinazione = f"{DIRECTORY_REPOS}{APACHE_PATH}{repository.get("name")}"

            Repo.clone_from(clone_url, path_destinazione)
            time.sleep(2)  # pause between projects to avoid overloading the Git server (and thus prevent being blocked)





    def clone_lpo_projects(self):
        repos_url = f"https://api.github.com/orgs/LPODISIM2024/repos?type=private"

        response = requests.get(repos_url, headers=header_git)
        repos = response.json()

        for repository in repos:
            url = repository.get("clone_url")
            print(f"Cloning {url}")
            path_destinazione = f"{DIRECTORY_REPOS}{LPO_PATH}{repository.get("name")}"

            Repo.clone_from(url, path_destinazione)
            time.sleep(2)  # pause between projects to avoid overloading the Git server (and thus prevent being blocked)



    def creation_sonar_projects(self, dir):

        for repository in os.listdir(dir):

            if repository.startswith("."):    #come cartella .git
                continue

            create_project(repository)




    def results_pre_refactoring(self, dir):

        for project in os.listdir(dir):

            if project.startswith("."):  #as .git
                continue

            returns_metrics_pre_kickoff(project)
            time.sleep(3)



    def results_post_refactoring(self, dir):

        for project in os.listdir(dir):

            if project.startswith("."):  #as .git
                continue

            returns_metrics_post_kickoff(project)
            time.sleep(3)

        final_report_excel()


