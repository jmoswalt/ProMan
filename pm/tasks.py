from celery import task

@task()
def print_out(x):
    print "task running: ", x
    return x