import os
from typing import Final

DIRECTORY= "././cloned_repos_lpo"
FILE_REPORT_PRE_REFACTORING = "attributes_before_refactoring"  #attributo privato
FILE_REPORT_POST_REFACTORING = "attributes_post_refactoring"  #attributo privato
FILE_REPORT_POST_REFACTORING_NEW_CODE = "attributes_new_code_post_refactoring"  #attributo privato
#header che contiene il token di SonarQube, usato in tutte le chiamate API
HEADER: Final[dict[str, str]] = {
    "Authorization": f"Bearer {os.getenv("SONAR_LOCAL_API_TOKEN")}",

}

header_git = {
            "Authorization": f"Bearer {os.getenv("GITHUB_API_TOKEN")}"
}
