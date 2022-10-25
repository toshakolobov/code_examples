import json
import re
from copy import deepcopy
from typing import Optional

import requests

from retry_decorator import retry


class MSSimpleAdaptiveCard():
    """
    Author: Anton Kolobov
    Description: a class to send messages via bot into Teams command channels
    """
    HEADERS = {
        'Content-Type': 'application/json'
    }
    JSON_TEMPLATE = {
        'type': 'message',
        'attachments': [
            {
                'contentType': 'application/vnd.microsoft.card.adaptive',
                'content': {
                    'type': 'AdaptiveCard',
                    '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
                    'version': '1.2',
                    'body': [],
                    'msteams': {
                        'width': 'full',
                        'entities': [],
                    },
                }
            }
        ]
    }

    def __init__(self, teams_wh_url: str):
        self.url = teams_wh_url
        self.message_dict = deepcopy(MSSimpleAdaptiveCard.JSON_TEMPLATE)
        self.users = {}

    def __str__(self):
        return self.msg

    def add_mention_user(self, user_email: str, display_name: str, alias: Optional[str] = None):
        # default alias: "<display_name> UPN"
        self.users[f'{display_name} UPN' if alias is None else alias] = {
            'name': display_name,
            'id': user_email,
            'imported': False,
        }

    def add_text_block(self, text: str, *, position: int = None, **kwargs):
        """
        usage: <class_instance>.add_text_block(text, size='large', color='warning', ...)
        Additional keywords (kwargs) described here: https://adaptivecards.io/explorer/TextBlock.html
        """
        text_block = {
            'type': 'TextBlock',
            'text': text.replace('\n', '\n\n\n\n \n\n\n\n'),
        }
        text_block.update(kwargs)
        if position is None:
            self.msg_body.append(text_block)
        else:
            self.msg_body.insert(position, text_block)

    def check(self):
        if not self.msg_body:
            raise NoTextBlockDetected('No text block has been added')

    def construct(self):
        self.msg_attachment_content['msteams']['entities'] = []
        for user in self.users.values():
            user['imported'] = False

        entities = self.msg_attachment_content['msteams']['entities']
        for text in (item['text'] for item in self.msg_body):
            for alias in re.findall(r'<at>(.+?)</at>', text):
                if alias in self.users.keys():
                    if self.users[alias]['imported'] is False:
                        entities.append({
                            'type': 'mention',
                            'text': f'<at>{alias}</at>',
                            'mentioned': {
                                'id': self.users[alias]['id'],
                                'name': self.users[alias]['name'],
                            }
                        })
                        self.users[alias]['imported'] = True
                else:
                    raise UserNotFoundError(f'Can\'t find user with alias "{alias}"')

    @retry(wait_ms=5000, limit=5, ex_types=(OSError, requests.exceptions.RequestException))
    def send(self):
        self.construct()
        self.check()
        response = requests.request("POST", self.url, headers=self.HEADERS, data=self.msg)
        response.raise_for_status()

    # properties
    @property
    def msg_attachments(self):
        return self.message_dict['attachments']

    @property
    def msg_attachment_content(self):
        return self.msg_attachments[0]['content']

    @property
    def msg_body(self):
        return self.msg_attachment_content['body']

    @property
    def msg(self):
        return json.dumps(self.message_dict)


class UserNotFoundError(Exception):
    pass


class NoTextBlockDetected(Exception):
    pass
