from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator,MaxValueValidator

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100,unique=True)
    description = models.TextField()

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name
    

class Product(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150,unique=True)
    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name='product')    
    description = models.TextField()
    price = models.DecimalField(max_digits=5,decimal_places=2)
    stock = models.PositiveBigIntegerField(default=1)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='products/%Y/%m/%d')
    #------------------> add old price and new price

    def __str__(self):
        return self.name
    
    def average_ratins(self):
        ratings = self.ratings.all()
        if ratings.count() > 0:
            return sum([r.rating for r in ratings])/ratings.count()
    

class Rating(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='ratings')
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating}"

class Cart(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # total price / total item

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.cart_items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='cart_items')
    product = models.ForeignKey(Product,on_delete=models.CASCADE)    
    quantity = models.PositiveBigIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
    def get_cost(self):
        return self.quantity*self.product.price
    

class Order(models.Model):
    STATUS = [
        ('pending','Pending'),
        ('processing','Processing'),
        ('shipped','Shipped'),
        ('delivered','Delivered'),
        ('canceled','Canceled'),
    ]
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=12)
    address = models.CharField(max_length=100)
    post_code = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    note = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    tns_id = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10,choices=STATUS)

    def __str__(self):
        return f"Order {self.id}"
    
    def get_total_cost(self):
        return sum(item.get_cost() for item in self.order_items.all())
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='order_items')
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity = models.PositiveBigIntegerField(default=1)
    price = models.DecimalField(max_digits=5,decimal_places=2)

    def get_cost(self):
        return self.quantity*self.product.price