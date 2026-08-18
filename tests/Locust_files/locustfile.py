from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    # 每个用户执行任务之间的等待时间（秒）
    wait_time = between(1, 3)

    @task
    def index_page(self):
        self.client.get("/")

    @task(2)
    def about_page(self):
        self.client.get("/api/login")
