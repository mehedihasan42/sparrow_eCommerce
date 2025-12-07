from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from .forms import RegistrationForm,RatingForm
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

