import django.dispatch


friendship_established = django.dispatch.Signal(
    providing_args=['instance']
)

friendship_terminated = django.dispatch.Signal(
    providing_args=['instance']
)
