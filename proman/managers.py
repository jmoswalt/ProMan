from django.db import models

class VersionManager(models.Manager):
    def get_query_set(self):
        return super(VersionManager, self).get_query_set().filter(version=False)

class TaskManager(VersionManager):
    def owner_id(self, id):
        return self.get_query_set().filter(owner_id=id)

    def project_id(self, id):
        return self.get_query_set().filter(project_id=id)

class ProjectManager(VersionManager):
    def owner_id(self, id):
        return self.get_query_set().filter(owner_id=id)

    def client_id(self, id):
        return self.get_query_set().filter(client_id=id)