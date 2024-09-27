from social_app.models import BlockDetail, FriendRequest
from social_app.serializers import FriendRequestSerializer


def process_request(user_profile, user_id):
    request_object, created = FriendRequest.objects.get_or_create(
        sender=user_profile, receiver_id=user_id
    )
    if created:
        return True, FriendRequestSerializer(request_object).data
    if request_object.is_rejected():
        if request_object.valid_for_re_request():
            request_object.make_pending()
            processed = True
            response = FriendRequestSerializer(request_object).data
        else:
            processed = False
            response = {"message": "Cool down time is not over"}
    elif request_object.is_accepted():
        processed = False
        response = {"message": "Already friends"}
    else:
        processed = False
        response = {"message": "Already requested"}
    return processed, response
