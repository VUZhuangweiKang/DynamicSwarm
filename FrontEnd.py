#!/usr/bin/env /usr/local/bin/python
# encoding: utf-8
# Author: Zhuangwei Kang

import os, sys
from flask import *

from Messenger import Messenger
import utl
from SystemEnv import *


app = Flask(__name__)

# define a publisher for publishing messages to GM
messenger = Messenger.ps_bind(FEZMQPORT)


def main():

    @app.route('/deploy')
    def deploy_containers():
        pass

    @app.route('/update')
    def update_containers():
        pass

    @app.route('/prepare')
    def prepare_containers():
        pass

    @app.route('/query_cluster')
    def query_cluster():
        pass

    app.run(host=utl.get_local_address(), port=FEFLASKPORT, debug=False)


if __name__ == '__main__':
    main()