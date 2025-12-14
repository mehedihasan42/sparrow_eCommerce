from .models import Cart

def cart_item_count(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            return {'total_cart_items':cart.get_total_item()}
        except Cart.DoesNotExist:    
             {'total_cart_items':0}
    return {'total_cart_items':0}     