from BTCRestApi import *
import json, sys

#### GLOBAL CONFIG VARIABLES
VERSION = '22.1p0'
INSTALL_LOCATION="E:/Program Files/BTC/ep{}/rcp/ep.exe".format(VERSION)
WORKSPACE = sys.argv[1]                      # the entrypoint directory must be passed as an argument
PROFILE_PATH = WORKSPACE + "/profile.epp"    # this points to a .epp profile FILE
REPORT_DIR = WORKSPACE + "/reports"          # this is a DIRECTORY, not a file

print('[BTC] Connecting to BTC EmbeddedPlatform... ', end='')
ep = EPRestApi(29268, INSTALL_LOCATION, VERSION)
print('done')

# Apply preferences to use the correct Matlab
preferences = [
    { 'preferenceName': 'GENERAL_MATLAB_VERSION', 'preferenceValue': 'CUSTOM' },
    { 'preferenceName': 'GENERAL_MATLAB_CUSTOM_VERSION', 'preferenceValue': 'MATLAB R2020b (64-bit)' },
]
ep.put_req('preferences', preferences)

##########------------------- STEP 1: import tl model -------------------##########
print('[BTC] Importing TargetLink Model... ', end='')
response = ep.post_req('profiles?discardCurrentProfile=true', )
tl_import_payload = {
    'tlModelFile': WORKSPACE + '/powerwindow_tl/powerwindow_tl_v04.slx',
    'tlInitScript': WORKSPACE + '/powerwindow_tl/start.m'
}
response = ep.post_req('architectures/targetlink', tl_import_payload)
print('done')


##########------------------- STEP 4: generate vectors -------------------##########
print('[BTC] Generating stimuli vectors... ', end='')
response = ep.get_req('coverage-generation/')
vector_generation_config = json.loads(response.content)
# overwriting defaults to only target Statement coverage
vector_generation_config['targetDefinitions'] = [ { 'label': 'Statement', 'enabled': True } ]
vector_generation_config['engineSettings']['engineAtg']['timeoutSecondsPerSubsystem'] = 15
for engine in vector_generation_config['engineSettings']['engineCv']['coreEngines']:
    if not engine['name'] == 'ISAT':
        engine['use'] = False
response = ep.post_req('coverage-generation/', vector_generation_config)
print('done')


##########------------------- STEP 5: B2B MIL vs SIL -------------------##########
print('[BTC] Running B2B Test MIL vs. SIL... ', end='')
response = ep.get_req('scopes/')
scopes = json.loads(response.content)
toplevelScopeUid = scopes[0]['uid']
response = ep.post_req('scopes/{}/b2b'.format(toplevelScopeUid), { 'refMode': 'TL MIL', 'compMode': 'SIL' })
b2b_test = json.loads(response.content)['result']
b2b_test_uid = b2b_test['uid']
print(b2b_test['verdictStatus'])


print('[BTC] Creating HTML reports... ', end='')
##########------------------- STEP 6: B2B Test Results HTML Report -------------------##########
response = ep.post_req('b2b/{}/b2b-reports'.format(b2b_test_uid))
b2b_report_uid = json.loads(response.content)['uid']
response = ep.post_req('reports/' + b2b_report_uid, { 'exportPath': REPORT_DIR, 'newName': 'B2BTestReport' })


##########------------------- STEP 7: B2B Coverage HTML Report -------------------##########
response = ep.post_req('scopes/{}/code-analysis-reports-b2b'.format(toplevelScopeUid))
coverage_report_uid = json.loads(response.content)['uid']
response = ep.post_req('reports/' + coverage_report_uid, { 'exportPath': REPORT_DIR, 'newName': 'CoverageReport' })
print('done')

if not b2b_test['verdictStatus'] == 'PASSED':
    raise Exception("B2B Test completed with verdict status " + b2b_test['verdictStatus'])

# when the ep object dies its garbage collector will automatically close everything for us :D
print("Finished with workflow.")