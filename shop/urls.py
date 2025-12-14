from django.urls import path,include
from . import views

urlpatterns = [
    # authentication urls
    path('login/',views.signin,name='signin'),
    path('register/',views.signup,name='signup'),
    path('logout/',views.logout,name='logout'),

    # product urls
    path('',views.home,name='home'),
    path('products/',views.product_list,name='product'),
    path('products/<slug:category_slug>/',views.product_list,name='product_category'),
    path('product/<slug:slug>/',views.product_details,name='product_details'),
    path('rate/<int:product_id>/',views.rate_product,name='rate_product'),

    # cart urls
    path('cart/',views.cart_details,name='cart_details'),
    path('cart/add/<int:product_id>/',views.cart_add,name='cart_add'),
    path('cart/delete/<int:product_id>/',views.cart_delete,name='cart_delete'),
    path('cart/update/<int:product_id>/',views.cart_update,name='cart_update'),

    # checkout
    path('checkout/',views.checkout,name='checkout'),
    path('checkout/process/',views.payment_process,name='payment_process'),
    path('payment/success/<int:order_id>/',views.payment_success,name='payment_success'),
    path('payment/fail/<int:order_id>/',views.payment_fail,name='payment_fail'),
    path('payment/cancel/<int:order_id>/',views.payment_calcel,name='payment_calcel'),
]
# http://localhost:8000/payment/success/18/