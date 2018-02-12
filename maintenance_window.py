#!/usr/bin/env python
#
# Copyright (c) 2016, PagerDuty, Inc. <info@pagerduty.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of PagerDuty Inc nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL PAGERDUTY INC BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Script to create/cancel/modify a maintenance window
# CLI Usage: ./recurring_maintenance_windows -h

import requests
import sys
import json
import dateutil.parser
from datetime import datetime, timedelta
import argparse

def create_headers(api_key,email):
        return {
            'Authorization': 'Token token=' + api_key,
            'Content-type': 'application/json',
            'Accept': 'application/vnd.pagerduty+json;version=2',
            'From': email
        }

def get_maintenance_windows(api_key, email, service_ids=None,filter='ongoing',query='Automatic Maintenance'):
    headers = create_headers(api_key,email)
    result = []
    options = {}
    if service_ids:
        options['service_ids[]'] = service_ids
    options['filter']=filter
    options['query']=query
    windows = requests.get('https://api.pagerduty.com/maintenance_windows', headers=headers, params=options)
    if windows.status_code == 200:
        result = json.loads(windows.content)['maintenance_windows']
    if len(result)==0:
        return False
    else:
        return result


def create_maintenance_windows(api_key, email, duration, service_ids):
    headers = create_headers(api_key,email)
    start = datetime.utcnow()
    end = start + timedelta(minutes=int(duration))
    payload = {
            'maintenance_window': {
                'type': 'maintenance_window',
                'start_time': start.isoformat(),
                'end_time': end.isoformat(),
                'description': 'Automatic Maintenance',
                'services': service_ids
            }
        }
    print 'Creating a ' + duration + ' minute maintenance window starting at ' + str(start)
    r = requests.post('https://api.pagerduty.com/maintenance_windows', headers=headers, data=json.dumps(payload))
    if r.status_code == 201:
        print 'Maintenance window with ID ' + r.json()['maintenance_window']['id'] + ' was successfully created'
    else:
        print 'Error: maintenance window creation failed!\nStatus code: ' + str(r.status_code) + '\nResponse: ' + r.text + '\nExiting...'
        sys.exit(1)

def get_args():
    parser = argparse.ArgumentParser(description='Maintenance')
    subparsers = parser.add_subparsers(help='Options')
    sp = subparsers.add_parser('add', help='Add a maintenance')
    sp.add_argument('-k','--key', required=True, help='Api key')
    sp.add_argument('-e','--email', required=True, help='User email')
    sp.add_argument('-d','--duration', required=True, help='Duration in seconds')
    sp.add_argument('-s','--service', required=True, help='PagerDuty service id')
    sp.set_defaults(cmd = 'add')
    sp = subparsers.add_parser('end', help='End maintenance')
    sp.set_defaults(cmd = 'end')
    sp.add_argument('-k','--key', required=True, help='Api key')
    sp.add_argument('-e','--email', required=True, help='User email')
    sp.add_argument('-s','--service', required=True, help='PagerDuty service id')
    sp = subparsers.add_parser('change', help='Change maintenance')
    sp.set_defaults(cmd = 'change')
    sp.add_argument('-k','--key', required=True, help='Api key')
    sp.add_argument('-e','--email', required=True, help='User email')
    sp.add_argument('-d','--duration', required=True, help='Duration in seconds')
    sp.add_argument('-s','--service', required=True, help='PagerDuty service id')
    return parser.parse_args()

def delete_maintenance(api_key, email, service_id):
    headers = create_headers(api_key,email)
    windows = get_maintenance_windows(api_key, email, service_id)
    if windows:
        for window in windows:
            r = requests.delete('https://api.pagerduty.com/maintenance_windows/'+str(window['id']), headers=headers)
            if r.status_code == 204:
                print('Maintenance window with ID: ' + str(window['id']) + ' deleted')
            else:
                print 'Error: maintenance window deletion failed!\nStatus code: ' + str(r.status_code) + '\nResponse: ' + r.text + '\nExiting...'
    else:
        print('Can\'t find any maintenance window for service: ' + str(service_id))
        sys.exit(1)

def update_maintenance(api_key, email, duration, service_id):
    headers = create_headers(api_key,email)
    windows = get_maintenance_windows(api_key, email, service_id)
    if windows:
        for window in windows:
            start = datetime.utcnow()
            end = start + timedelta(minutes=int(duration))
            payload = {
                    'maintenance_window': {
                        'type': 'maintenance_window',
                        'end_time': end.isoformat()
                    }
                }
            r = requests.put('https://api.pagerduty.com/maintenance_windows/'+str(window['id']), headers=headers, data=json.dumps(payload))
            if r.status_code == 200:
                print('Maintenance\'s window with ID: ' + str(window['id']) + ' end time is: ' + str(end.isoformat()) + ' UTC')
            else:
                print 'Error: maintenance window deletion failed!\nStatus code: ' + str(r.status_code) + '\nResponse: ' + r.text + '\nExiting...'
                sys.exit(1)


if __name__ == '__main__':
    args = get_args()
    if args.cmd == 'add':
        create_maintenance_windows(args.key, args.email, args.duration, [{'id': args.service,'type': 'service_reference'}])
        sys.exit()
    elif args.cmd == 'end':
        delete_maintenance(args.key, args.email, args.service)
        sys.exit()
    elif args.cmd == 'change':
        update_maintenance(args.key, args.email, args.duration, args.service)
