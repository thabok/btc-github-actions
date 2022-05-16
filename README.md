# btc-github-actions
Repo to demonstrate how to use BTC EmbeddedPlatform with Github Actions.

## Relevant config files
- ".github/workflows/test-workflow.yml" describes the environment and the workflow steps
  - a self-hosted runner is used with Windows 10, Matlab R2020b, dSPACE TargetLink 5.1 and BTC EmbeddedPlatform 22.1
  - the main workflow step invokes a python script called "workflow.py" on the root of the repo

- the "workflow.py" script defines a test workflow with BTC EmbeddedPlatform using a wrapper class EPRestApi, defined in "EPRestApi.py"
- the class "EPRestApi" provides methods to start, stop and interact with BTC EmbeddedPlatform
