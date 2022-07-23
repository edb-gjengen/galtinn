from rest_framework import serializers

from dusken.apps.mailchimp.models import MailChimpSubscription


class MailChimpSubscriptionSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(
        default=MailChimpSubscription.STATUS_DEFAULT, choices=MailChimpSubscription.STATUS_CHOICES
    )

    class Meta:
        model = MailChimpSubscription
        fields = ("email", "status")

    def create(self, validated_data):
        sub, created = MailChimpSubscription.objects.get_or_create(
            email=validated_data.get("email"), defaults={"status": MailChimpSubscription.STATUS_DEFAULT}
        )

        if not created:
            sub.status = MailChimpSubscription.STATUS_DEFAULT
            sub.save()

        sub.sync_to_mailchimp()

        return sub

    def update(self, instance, validated_data):
        new_status = validated_data.get("status")
        if instance.status != new_status:
            instance.status = new_status
            instance.save()
            instance.sync_to_mailchimp()

        return instance
