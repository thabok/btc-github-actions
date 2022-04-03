from BTCRestApi import *
import json, sys

#### GLOBAL CONFIG VARIABLES
VERSION = '22.1p0'
INSTALL_LOCATION="E:/Program Files/BTC/ep{}/rcp/ep.exe".format(VERSION)
WORKSPACE = sys.argv[1]                      # the entrypoint directory must be passed as an argument
PROFILE_PATH = WORKSPACE + "/profile.epp"    # this points to a .epp profile FILE
REPORT_DIR = WORKSPACE + "/reports"          # this is a DIRECTORY, not a file

ep = EPRestApi(29268, INSTALL_LOCATION, VERSION)

# Apply preferences to use the correct Matlab
preferences = [
    { 'preferenceName': 'GENERAL_MATLAB_VERSION', 'preferenceValue': 'CUSTOM' },
    { 'preferenceName': 'GENERAL_MATLAB_CUSTOM_VERSION', 'preferenceValue': 'MATLAB R2020b (64-bit)' },
]
ep.put_req('preferences', preferences)

##########------------------- STEP 1: open existing project -------------------##########
# open existing profile
response = ep.get_req('profiles/' + PROFILE_PATH)


##########------------------- STEP 2: update architecture -------------------##########
response = ep.put_req('architectures/')


##########------------------- STEP 3: run req.-based tests -------------------##########
response = ep.get_req('test-cases-rbt')
test_cases = json.loads(response.content)
rbt_execution_info = {}
rbt_execution_info.UIDs = [tc.uid for tc in test_cases]
rbt_execution_info.data = {}
rbt_execution_info.data.executionConfigNames = [ "TL MIL", "SIL" ]
response = ep.post_req('test-cases-rbt/test-execution-rbt')


##########------------------- STEP 4: generate vectors -------------------##########
response = ep.get_req('coverage-generation/')
vector_generation_config = json.loads(response.content)
# overwriting defaults to only target Statement coverage
vector_generation_config['targetDefinitions'] = [ { 'label': 'Statement', 'enabled': True } ]
response = ep.post_req('coverage-generation/', vector_generation_config)


##########------------------- STEP 5: B2B MIL vs SIL -------------------##########
response = ep.get_req('scopes/')
scopes = json.loads(response.content)
toplevelScopeUid = scopes[0]['uid']
response = ep.post_req('scopes/{}/b2b'.format(toplevelScopeUid), { 'refMode': 'TL MIL', 'compMode': 'SIL' })
b2b_test_uid = json.loads(response.content)['result']['uid']


##########------------------- STEP 6: B2B Test Results HTML Report -------------------##########
response = ep.post_req('b2b/{}/b2b-reports'.format(b2b_test_uid))
b2b_report_uid = json.loads(response.content)['uid']
response = ep.post_req('reports/' + b2b_report_uid, { 'exportPath': REPORT_DIR, 'newName': 'B2BResults.html' })


##########------------------- STEP 7: B2B Coverage HTML Report -------------------##########
response = ep.post_req('scopes/{}/code-analysis-reports-b2b'.format(toplevelScopeUid))
coverage_report_uid = json.loads(response.content)['uid']
response = ep.post_req('reports/' + coverage_report_uid, { 'exportPath': REPORT_DIR, 'newName': 'B2BCoverage.html' })

# when the ep object dies its garbage collector will automatically close everything for us :D
print("Finished with workflow.")