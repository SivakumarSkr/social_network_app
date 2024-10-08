from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone
import uuid
from django.db.models import QuerySet
from django.conf import settings
from datetime import timedelta
from django.db.models import Subquery


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150)
    first_name = None
    last_name = None
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email}"


class BaseModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserProfileQuerySet(models.QuerySet):
    def remove_block_users(self, user):
        blockers = BlockDetail.objects.filter(blocked=user).values('blocker')
        return self.exclude(uuid__in=Subquery(blockers))


class UserProfileManager(models.Manager):
    def get_queryset(self):
        return UserProfileQuerySet(self.model, using=self._db)


class UserProfile(BaseModel):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="user_profile"
    )
    friends = models.ManyToManyField(
        "self", symmetrical=False, related_name="following", blank=True
    )
    objects = UserProfileManager()

    def __str__(self):
        return f"{self.user.name}"

    def get_friends(self) -> QuerySet["UserProfile"]:
        return self.friends.all()


class RequestStatus(models.TextChoices):
    PENDING = "P", "Pending"
    ACCEPTED = "A", "Accepted"
    REJECTED = "R", "Rejected"


class FriendRequest(BaseModel):
    sender = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="sent_requests"
    )
    receiver = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="received_requests"
    )
    status = models.CharField(
        max_length=1, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )
    cooldown_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("sender", "receiver")

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"

    def make_accepted(self) -> None:
        self.sender.friends.add(self.receiver)
        self.status = RequestStatus.ACCEPTED
        self.save()

    def make_rejected(self) -> None:
        self.status = RequestStatus.REJECTED
        cooldown_time = timezone.now() + timedelta(seconds=settings.COOLDOWN_TIME)
        self.cooldown_time = cooldown_time
        self.save()

    def not_in_pending(self) -> bool:
        return self.status != RequestStatus.PENDING
    
    def is_rejected(self):
        return self.status == RequestStatus.REJECTED

    def valid_for_re_request(self):
        return self.cooldown_time < timezone.now()

    def make_pending(self):
        self.status = RequestStatus.PENDING
        self.cooldown_time = None
        self.save()

    def is_accepted(self):
        return self.status == RequestStatus.ACCEPTED
    

class BlockDetail(BaseModel):
    blocker = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='blocked_details')
    blocked = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("blocker", "blocked")