from google.appengine.api import users
import logging


def check_user(controller):
    """
        Check and Get user info
        """
    if 'application_user_key' not in controller.session:
        return True
    check_target = 'application_user_key'
    if controller.session[check_target] is None:
        return True
    application_user = controller.session[check_target].get()
    if application_user is None:
        return True
    controller.application_user = application_user
    controller.context[check_target] = application_user.key
    controller.context['user'] = application_user
    return True


def require_user(controller):
    """
        Requires that a user is logged in
        """
    if 'application_user_key' not in controller.session:
        return False, 'require_user'
    application_user = controller.session['application_user_key'].get()
    if application_user is None:
        return False, 'require_user'
    controller.application_user = application_user
    controller.context['application_user_key'] = application_user.key
    action_name = '.'.join(str(controller).split(' object')[0][1:].split('.')[0:-1]) + '.' + controller.route.action

    if controller.application_user.has_permission(action_name) is False:
        return controller.abort(403)
    return True


def require_admin(controller):
    """
    Requires that a user is logged in and that the user is and administrator on the App Engine Application
    """
    admin_user = None
    if 'application_admin_user_key' not in controller.session:
        return False, 'require_admin'
    if controller.session['application_admin_user_key'] is not None:
        admin_user = controller.session['application_admin_user_key'].get()
    if admin_user is None:
        return False, 'require_admin'
    controller.application_user = admin_user
    controller.context['application_user_key'] = admin_user.key
    action_name = '.'.join(str(controller).split(' object')[0][1:].split('.')[0:-1]) + '.' + controller.route.action

    if controller.application_user.has_permission(action_name) is False:
        return controller.abort(403)
    return True


def predicate_chain(predicate, chain):
    """
    Returns the result of chain if predicate returns True, otherwise returns True.
    """

    def inner(*args, **kwargs):
        predicate_curried = predicate(*args, **kwargs)

        def inner_inner(controller):
            if predicate_curried(controller):
                return chain(controller)
            return True

        return inner_inner

    return inner


def prefix_predicate(prefix):
    prefix = prefix if isinstance(prefix, (list, tuple)) else (prefix,)

    def inner(controller):
        if controller.route.prefix in prefix:
            return True
        return False
    return inner


def action_predicate(action):
    action = action if isinstance(action, (list, tuple)) else (action,)

    def inner(controller):
        if controller.route.action in action:
            return True
        return False
    return inner


def route_predicate(route):
    route = route if isinstance(route, (list, tuple)) else (route,)

    def inner(controller):
        route_name = controller.route.name.split(':')[0]
        if route_name in route:
            return True
        return False
    return inner


check_user_for_prefix = predicate_chain(prefix_predicate, check_user)
check_user_for_action = predicate_chain(action_predicate, check_user)
check_user_for_route = predicate_chain(route_predicate, check_user)

require_user_for_prefix = predicate_chain(prefix_predicate, require_user)
require_user_for_action = predicate_chain(action_predicate, require_user)
require_user_for_route = predicate_chain(route_predicate, require_user)

require_admin_for_prefix = predicate_chain(prefix_predicate, require_admin)
require_admin_for_action = predicate_chain(action_predicate, require_admin)
require_admin_for_route = predicate_chain(route_predicate, require_admin)

