from twisted.internet import defer, reactor
from txboxdotnet.api_v2 import txBoxAPI

api = txBoxAPI(
    client_id='...',
    client_secret='...', ... )

if not api.auth_code:
    print '\n'.join([
        'Visit the following URL in any web browser (firefox, chrome, safari, etc),',
            '  authorize there, confirm access permissions, and paste URL of an empty page',
            '  (starting with "https://success.box.com/") you will get',
            '  redirected to into "auth_code" value in "config" dict above.\n',
        'URL to visit:\n  {}'.format(api.auth_user_get_url()) ])
    exit()

if re.search(r'^https?://', api.auth_code):
    api.auth_user_process_url(api.auth_code)

@defer.inlineCallbacks
def do_stuff():

    # Print root directory listing
    print list(e['name'] for e in (yield api.listdir()))

    # Upload "test.txt" file from local current directory
    file_info = yield api.put('test.txt')

    # Find just-uploaded "test.txt" file by name
    file_id = yield api.resolve_path('test.txt')

    # Check that id matches uploaded file
    assert file_info['id'] == file_id

    # Remove the file
    yield api.delete(file_id)

do_stuff().addBoth(lambda ignored: reactor.stop())
reactor.run()

#destFol = '406600304'
#ret = box.uploadFile((('Z:/PROJECTS/V2_Parcels/Final_Deliverables/V2.0.1_Wisconsin_Parcels_2016_by_County/V201_Wisconsin_Parcels_BARRON/V201_Wisconsin_Parcels_BARRON_SHP.zip', 'test_SHP.zip'),), destFol)
