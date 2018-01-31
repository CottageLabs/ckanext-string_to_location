from functools import wraps
import mock

'''
For end-to-end tests to pass, we need the background job to run synchronously rather than asynchronously.
Below we are mocking the ckan.plugins.toolkit.enqueue_job function to execute jobs immediately upon being called
rather than put them on a queue to be picked up on a later date.

Many thanks to Florian Brucker who pointed out this approach on the ckan-dev mailing list!
'''

def sequential_enqueue(job_func, args=None, kwargs=None, title=None):
    args = args or []
    kwargs = kwargs or {}
    job_func(*args, **kwargs)

    class MockJob(object):
        id = "testid"
    job = MockJob()

    return job

'''
Instead of making each test do its own mocking, the decorator defined below wraps
any function given to it with a patch that replaces ckan.plugins.toolkit.enqueue_job with
our custom queueing function sequential_enqueue defined above.
'''

def with_sequential_rq(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with mock.patch('ckan.plugins.toolkit.enqueue_job', side_effect=sequential_enqueue):
            return f(*args, **kwargs)
    return wrapper
