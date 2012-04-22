from time import strftime

def get_task_change_message(old=None, new=None):
    if old and new:
        output = ""
        if old.title != new.title:
            output = output + 'changed <span class="task-field">Title</span> from <span class="task-change-old">%s</span> to <span class="task-change-new">%s</span>, ' % (old.title, new.title)

        if old.description != new.description:
            output = output + 'changed the <span class="task-field">Description</span>, '

        if old.assignee != new.assignee:
            output = output + '<span class="task-field">Reassigned</span> this from <span class="task-change-old">%s</span> to <span class="task-change-new">%s</span>, ' % (old.assignee, new.assignee)

        if old.due_dt != new.due_dt:
            output = output + 'changed <span class="task-field">Due Date</span> from <span class="task-change-old">%s</span> to <span class="task-change-new">%s</span>, ' % (old.due_dt.strftime("%m/%d/%Y"), new.due_dt.strftime("%m/%d/%Y"))

        if old.task_time != new.task_time:
            output = output + 'changed <span class="task-field">Task Time</span> from <span class="task-change-old">%s</span> to <span class="task-change-new">%s</span>, ' % (old.task_time, new.task_time)

        if old.status != new.status:
            if new.status == "Done":
                output = output + '<span class="task-change-new">Closed</span> the task from <span class="task-change-old">%s</span>, ' % (old.status)
            elif old.status == "Done":
                output = output + '<span class="task-change-old">Reopened</span> the task to <span class="task-change-new">%s</span>, ' % (new.status)
            else:
                output = output + 'changed <span class="task-field">Status</span> from <span class="task-change-old">%s</span> to <span class="task-change-new">%s</span>, ' % (old.status, new.status)

        if old.resolution != new.resolution:
            output = output + 'changed the <span class="task-field">Resolution</span>, '

        if old.private != new.private:
            if new.private:
                output = output + 'changed this to <span class="task-field-private">Private</span>, '
            else:
                output = output + 'changed this to <span class="task-field-public">Public</span>, '

        if old.billable != new.billable:
            if new.billable:
                output = output + 'changed this to <span class="task-field-billable">Billable</span>, '
            else:
                output = output + 'changed this to <span class="task-field-non-billable">Non Billable</span>, '

        if not output:
            return "made no changes"
        return output[:-2]
    return "Edited Task"