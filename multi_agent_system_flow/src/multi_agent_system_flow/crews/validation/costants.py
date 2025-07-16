import os
from typing import Final

DIRECTORY_REPOS= "././cloned_repos"
LPO_PATH = "/lpo/"
APACHE_PATH = "/apache/"
FILE_REPORT_PRE_REFACTORING = "attributes_before_refactoring"
FILE_REPORT_POST_REFACTORING = "attributes_post_refactoring"

CLASSES_TO_REFACTOR = 5      #only for RQ1 and RQ2
METRIC_TO_REFACTOR = "bugs"    #"bugs", "code_smells", "vulnerabilities", .....  only for RQ3


#header that contain SonarQube token, used in all API calls
HEADER: Final[dict[str, str]] = {
    "Authorization": f"Bearer {os.getenv("SONAR_LOCAL_API_TOKEN")}",

}

#header that contain GitHub token, used in GitHub API calls
header_git = {
            "Authorization": f"Bearer {os.getenv("GITHUB_API_TOKEN")}"
}
