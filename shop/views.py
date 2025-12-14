from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout as django_logout
from django.contrib import messages
from .forms import RegistrationForm,RatingForm,CheckoutForm
from . import models
from django.db.models import Max,Min,Avg,Q
from . import sslcommerz
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
# filter on price,category,rating

# Create your views here.
def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request,username=username,password=password)

        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,'Invalid User')
    return render(request,'shop/signin.html')


def signup(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request,user)
            messages.success(request,'Sign Up successfull')
            return redirect('home')
    else:
        form = RegistrationForm()    
    return render(request,'shop/signup.html',{'form':form})    


def logout(request):
    django_logout(request)
    return redirect('signin')


def home(request):
    featured_product = models.Product.objects.filter(
        available=True
    ).order_by('-created_at')[:4]

    categories = models.Category.objects.all()

    # SHOW ALL PRODUCTS BY DEFAULT
    products = models.Product.objects.filter(available=True)

    # APPLY FILTERS ONLY IF USER SELECTS
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    rating = request.GET.get('rating')

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    if rating:
        products = products.annotate(
            avg_rating=Avg('ratings__rating')
        ).filter(avg_rating__gte=rating)

    context = {
        'featured_product': featured_product,
        'categories': categories,
        'products': products,
    }

    return render(request, 'shop/home.html', context)


def product_list(request,category_slug=None):
    category = None
    categories = models.Category.objects.all()
    products = models.Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(models.Category,slug=category_slug)
        products = products.filter(category=category)

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

    return render(request,'shop/home.html',context) 


def product_details(request,slug):
    product = get_object_or_404(models.Product,slug=slug,available=True)
    related_product = models.Product.objects.filter(category=product.category).exclude(id=product.id)

    user_rating = None
    rating_form = None
    
    if request.user.is_authenticated:
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
    
    return render(request,'shop/product_details.html',context)

@login_required
def rate_product(request, product_id):
    product = get_object_or_404(models.Product, id=product_id)

    # Check if user purchased the product
    order_item = models.OrderItem.objects.filter(
        order__user=request.user,
        product=product,
        order__paid=True
    )

    if not order_item.exists():
        messages.warning(request, 'You can only rate products you have purchased!')
        return redirect('home')

    # Get existing rating (if any)
    rating = models.Rating.objects.filter(
        product=product,
        user=request.user
    ).first()

    if request.method == 'POST':
        form = RatingForm(request.POST, instance=rating)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.product = product
            rating.user = request.user
            rating.save()
            messages.success(request, 'Thank you for your rating!')
            return redirect('home')
    else:
        form = RatingForm(instance=rating)

    context = {
        'form': form,
        'product': product
    }

    return render(request, 'rate_product.html', context)  

@login_required
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
    return redirect('cart_details')       

@login_required
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
    return redirect('cart_details')     

@login_required
def cart_delete(request,product_id):
    cart = get_object_or_404(models.Cart,user=request.user)
    product = get_object_or_404(models.Product,id=product_id)
    cart_item = get_object_or_404(models.CartItem,cart=cart,product=product)
    cart_item.delete()
    messages.success(request,f'{product.name} has been deleted successfully')
    return redirect('cart_details')

@login_required
def cart_details(request):
    try:
        cart = models.Cart.objects.get(user=request.user)
    except models.Cart.DoesNotExist:
        cart = models.Cart.objects.create(user=request.user)    
    return render(request,'shop/cart_details.html',{'cart':cart})    

@login_required
def checkout(request):
    try:
       cart = models.Cart.objects.get(user=request.user)
       if not cart.cart_items.exists():
           messages.warning(request,'Your cart is empty')
           return redirect('home')
    except models.Cart.DoesNotExist:   
        messages.warning(request,"Your cart doesn't exists")
        return redirect('home')
    
    if request.method == 'POST':
      form = CheckoutForm(request.POST)
      if form.is_valid():
        order = form.save(commit=False)
        order.user = request.user
        order.save()

        for item in cart.cart_items.all():
            models.OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )

        cart.cart_items.all().delete()
        request.session['order_id'] = order.id
        return redirect('payment_process')
   
    else:
        form = CheckoutForm()
    context = {
        'cart':cart,
        'form':form
    }    
    return render(request,'shop/checkout.html',context)    


def payment_process(request):
    order_id = request.session.get('order_id')

    if not order_id:
        messages.error(request, 'No order id exists')
        return redirect('home')

    order = get_object_or_404(models.Order, id=order_id)

    # Generate SSLCommerz payment (this usually returns a redirect URL or form)
    payment_data = sslcommerz.generate_sslcommerz_payment(request, order)

    if payment_data['status'] == 'SUCCESS':
        return redirect(payment_data['GatewayPageURL'])
    else:
        messages.error(request, 'Payment gateway error')
        return redirect('checkout')

@csrf_exempt
def payment_success(request, order_id):
    order = get_object_or_404(models.Order, id=order_id)

    # Prevent duplicate processing
    if order.paid:
        return render(request, 'payment_success.html', {'order': order})

    order.paid = True
    order.status = 'processing'
    order.tns_id = order.id
    order.save()

    for item in order.order_items.all():
        product = item.product
        product.stock -= item.quantity
        if product.stock < 0:
            product.stock = 0
        product.save()

    messages.success(request, 'Payment successful')
    return render(request, 'shop/payment_success.html', {'order': order})

@csrf_exempt
def payment_fail(request,order_id):
    order = get_object_or_404(models.Order,id=order_id)
    order.status = 'canceled'
    order.save()
    messages.warning(request,'Sorry Sir,Your payment is failed! Please try again.')
    return redirect('home')

@csrf_exempt
def payment_calcel(request,order_id):
    order = get_object_or_404(models.Order,id=order_id,user=request.user)
    order.status = 'canceled'
    order.save()
    messages.error(request,'Sorry Sir,Your payment is failed! Please try again.')
    return redirect('home')

# -----SSL---------
# 54mehedi233
# hasan0011
# ------app password-------
# MH Sparrow 
# uafc gzkj fesu kqro
