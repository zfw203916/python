class car:
    def __init__(self, color: str, speed: int, model: str, price: float):
        self.color = color
        self.speed = speed
        self.model = model
        self.price = price

    # 定义实例方法，一个方法来运行汽车
    def run(self):
        print(
            f"The {self.color} {self.model} is running at {self.speed} km/h and costs ${self.price}."
        )

    def total_price(self, tax_rate: float) -> float:
        """
        计算汽车的总价格，包括税费。
        :param tax_rate: 税率（例如，0.1 表示 10% 的税）
        :return: 总价格
        """
        total = self.price * (1 + tax_rate)
        return total


car1 = car(color="red", speed=150, model="Sedan", price=20000.0)
car1.run()
print(f"Car 1's total price with 10% tax: ${car1.total_price(0.1)}")
