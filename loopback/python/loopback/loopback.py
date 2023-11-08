# -*- mode: python; python-indent: 4 -*-
import ncs
import ipaddress
from ncs.application import Service


class ServiceCallbacks(Service):
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')')

        management_prefix = service.management_prefix
        self.log.debug(f'Value of management-prefix leaf is {management_prefix}')
        net = ipaddress.IPv4Network(management_prefix)
        management_address = list(net.hosts())[0]

        bgp_prefix = service.bgp_prefix
        self.log.debug(f'Value of bgp-prefix leaf is {bgp_prefix}')
        net = ipaddress.IPv4Network(bgp_prefix)
        bgp_address = list(net.hosts())[0]
        vars = ncs.template.Variables()
        vars.add('MANAGEMENT_ADDRESS', management_address)
        vars.add('BGP_ADDRESS', bgp_address)
        template = ncs.template.Template(service)
        template.apply('loopback-template', vars)

# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Loopback(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us. It is accessible
        # through 'self.log' and is a ncs.log.Log instance.
        self.log.info('Loopback RUNNING')

        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        #
        self.register_service('loopback-servicepoint', ServiceCallbacks)
