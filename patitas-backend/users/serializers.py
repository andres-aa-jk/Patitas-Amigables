from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Datos públicos del usuario que consume el React."""

    id = serializers.CharField(read_only=True)
    rol = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "direccion", "numero", "rol")
        read_only_fields = ("id", "rol")

    def get_rol(self, obj):
        # El rol solo se asigna desde el panel de administración, nunca desde la API.
        return "admin" if obj.es_admin else "usuario"


class RegisterSerializer(serializers.ModelSerializer):
    """Equivale a UserRegistrationForm del proyecto Django original."""

    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    direccion = serializers.CharField(required=True)
    numero = serializers.CharField(required=True, max_length=20)
    acepta_politica = serializers.BooleanField(required=True)

    class Meta:
        model = User
        fields = (
            "username", "email", "direccion", "numero",
            "password1", "password2", "acepta_politica",
        )

    def validate_acepta_politica(self, value):
        if value is not True:
            raise serializers.ValidationError(
                "Debes aceptar la política de tratamiento de datos personales."
            )
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ese nombre de usuario ya existe.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ese correo ya está registrado.")
        return value

    def validate(self, attrs):
        if attrs["password1"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password2": "Las contraseñas no coinciden."}
            )
        validate_password(attrs["password1"])
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password1")
        user = User(**validated_data)
        user.fecha_aceptacion = timezone.now()
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Equivale a UserEditForm."""

    class Meta:
        model = User
        fields = ("username", "email", "direccion", "numero")

    def validate_username(self, value):
        qs = User.objects.filter(username=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ese nombre de usuario ya existe.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual no es correcta.")
        return value

    def validate(self, attrs):
        if attrs["new_password1"] != attrs["new_password2"]:
            raise serializers.ValidationError(
                {"new_password2": "Las contraseñas nuevas no coinciden."}
            )
        validate_password(attrs["new_password1"], self.context["request"].user)
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password1"])
        user.save()
        return user


class PatitasTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Devuelve también los datos del usuario junto con los tokens."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
