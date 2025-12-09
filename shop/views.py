from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from .forms import RegistrationForm,RatingForm,CheckoutForm
from . import models
from django.db.models import Max,Min,Avg,Q
# filter on price,category,rating

# Create your views here.
def signin(request):
    if request.method == 'POST':
        username = request.Post.get('username')
        password = request.Post.get('password')

        user = authenticate(request,username=username,password=password)

        if user is not None:
            login(request,user)
            return redirect('')
        else:
            messages.error(request,'Invalid User')
    return render(request,'')


def signup(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request,user)
            messages.success(request,'Sign Up successfull')
            return redirect('')
    else:
        form = RegistrationForm()    
    return render(request,'',{'form':form})    


def logout(request):
    logout(request)
    return render('')


def home(request):
    featured_product = models.Product.objects.filter(available=True).order_by('-created_at')[:8]
    categories = models.Category.objects.all()

    context = {
        'featured_product':featured_product,
        'categories':categories
    }

    return render(request,'',context)


def product_list(request,category_slug=None):
    category = None
    categories = models.Category.objects.all()
    products = models.Product.objects.all()

    if category_slug:
        category = get_object_or_404(models.Category,category_slug)
        products = models.Product.objects.filter(category)

    min_price = products.aggregate(Min('price'))['price__min']
    max_price = products.aggregate(Max('price'))['price__max']

    if request.GET.get('min_price'):
        products = products.filter(price__gte=request.GET.get('min_price'))

    if request.GET.get('max_price'):
       products = products.filter(price__lte=request.GET.get('max_price'))

    if request.GET.get('rating'):
        products = products.annotate(avg_rating = Avg('ratings__rating')).filter(avg_rating=request.GET.get('rating')) 

    if request.GET.get('search'):
        query = request.GET.get('search')
        products = products.filter(
            Q(name__icontains = query) |
            Q(description__icontains = query) |
            Q(category__name__icontains = query) 
        )

    context = {
        'category':category,
        'categories':categories,
        'min_price':min_price,
        'max_price':max_price,
        'products':products
    }   

    return render(request,'',context) 


def product_details(request,slug):
    product = get_object_or_404(models.Product,slug=slug,available=True)
    related_product = models.Product.objects.filter(category=product.category).exclude(id=product.id)

    user_rating = None

    try:
        user_rating = models.Rating.objects.get(product=product,user=request.user)
    except models.Rating.DoesNotExist:
        pass
    rating_form = RatingForm(instance=user_rating)  

    context = {
        'product':product,
        'related_product':related_product,
        'user_rating':user_rating,
        'rating_form':rating_form
    }  
    
    return render(request,'',context)


def rate_product(request,product_id):
    product = get_object_or_404(models.Product,id = product_id)

    order_item = models.OrderItem.objects.filter(
        order__user = request.user,
        product = product,
        order__paid = True
    )

    if not order_item.exists():
        messages.warning(request,'You can only rate product you have purchased!')
        return redirect('')
    
    try:
        rating = models.Rating.objects.filter(product=product,user=request.user)
    except models.Rating.DoesNotExist:
        rating = None    

    if request.method == 'POST':
        form = RatingForm(user=request.user,instance=rating)
        rating = form.save(commit=False)
        rating.product = product
        rating.user = request.user
        rating.save()
        return redirect('')
    else:
        form = RatingForm(instance=rating)

    context = {
        'form':form,
        'product':product
    }    

    return render(request,'',context)    


def cart_add(request,product_id):
    product = get_object_or_404(models.Product,id=product_id)

    try:
        cart = models.Cart.objects.get(user=request.user)
    except models.Cart.DoesNotExist:
        cart = models.Cart.objects.create(user=request.user)    

    try:
        cart_item = models.CartItem.objects.get(cart=cart,product=product)
        cart_item.quantity += 1
        cart_item.save()
    except models.CartItem.DoesNotExist:
        models.CartItem.objects.create(cart=cart,product=product,quantity = 1)    

    messages.success(request,f'{product.name} has been added successfully')
    return redirect('')       


def cart_update(request,product_id):
    cart = get_object_or_404(models.Cart,user=request.user)
    product = get_object_or_404(models.Product,id=product_id)
    cart_item = get_object_or_404(models.CartItem,cart=cart,product=product)

    quantity = int(request.POST.get('quantity',1))

    if quantity <= 0:
        cart_item.delete()
        messages.success(request,f'{product.name} has been deleted from your cart')    
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request,'Cart updated successfully')
    return redirect('')     


def cart_delete(request,product_id):
    cart = get_object_or_404(models.Cart,user=request.user)
    product = get_object_or_404(models.Product,id=product_id)
    cart_item = get_object_or_404(models.CartItem,cart=cart,product=product)
    cart_item.delete()
    messages.success(request,f'{product.name} has been deleted successfully')
    return redirect('')


def cart_details(request):
    try:
        cart = models.Cart.objects.get(user=request.user)
    except models.Cart.DoesNotExist:
        cart = models.Cart.objects.create(user=request.user)    
    return render(request,'',{'cart':cart})    


def checkout(request):
    try:
       cart = models.Cart.objects.get(user=request.user)
       if not cart.cart_items.exists():
           messages.warning(request,'Your cart is empty')
           return redirect('')
    except models.Cart.DoesNotExist:   
        messages.warning(request,"Your cart doesn't exists")
        return redirect('')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
          order = form.save(commit=False)
          order.user = request.user
          order.save()

        for item in cart.cart_items.all():
           models.OrderItem.objects.create(
           order = order,
           product = item.product,
           price = item.product.price,
           quantity = item.quantity
         )
    
        cart.cart_items.all().delete()    
        request.session['order_id'] = order.id  
        return redirect('')
   
    else:
        form = CheckoutForm()
    context = {
        'cart':cart,
        'form':form
    }    
    return render(request,'',context)     


def payment_success(request,order_id):
    order = get_object_or_404(models.Order,id=order_id,user=request.user)     
    order.paid = True  
    order.status = 'processing'
    order.tns_id = order.id
    order.save()
    order_item = order.order_items.all()

    for item in order_item:
        product = item.product
        product.stock -= item.quantity

    if product.stock < 0:
        product.stock = 0
    product.save()    

    messages.success(request,'Payment successfull')

    return render(request,'',{'order':order})


def payment_fail(request,order_id):
    order = get_object_or_404(models.Order,id=order_id,user=request.user)
    order.status = 'canceled'
    order.save()
    return redirect('')

def payment_calcel(request,order_id):
    order = get_object_or_404(models.Order,id=order_id,user=request.user)
    order.status = 'canceled'
    order.save()
    return redirect('')

