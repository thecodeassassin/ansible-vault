import os
import urllib2
import json
import sys
import subprocess
from urlparse import urljoin

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):
        key = terms[0]

        url = os.getenv('VAULT_ADDR')
        if not url:
            raise AnsibleError('VAULT_ADDR environment variable is missing')

        token = os.getenv('VAULT_TOKEN')
        if not token:
            raise AnsibleError('VAULT_TOKEN environment variable is missing')

        request_url = urljoin(url, "v1/%s" % (key))
        try:
            # when using http (tlsv1.2) connections wrap curl since python <2.7.9 doesnt support tlsv1.2
            if "https" in url:
                output = subprocess.Popen(["curl", "-s", "-XGET", "-H", "X-Vault-Token: %s" % token, "%s" % request_url], stdout=subprocess.PIPE).communicate()[0]
            else:
                headers = { 'X-Vault-Token' : token }
                req = urllib2.Request(request_url, None, headers)
                response = urllib2.urlopen(req)
                output = response.read()
        except urllib2.HTTPError as e:
            raise AnsibleError('Unable to read %s from vault: %s' % (key, e))
        except:
            raise AnsibleError('Unable to read %s from vault' % key)

        result = json.loads(output)

        if 'data' not in result:
            raise AnsibleError('Key %s not found in vault' % key)

        return [result['data']['value']]
