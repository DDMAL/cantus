from typing import Any, Type

from django.db.models.query import QuerySet
from rest_framework import generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.throttling import ScopedRateThrottle

from cantusdata.models.mei_submission import MEISubmission
from cantusdata.serializers.mei_submission import (
    MEISubmissionCreateSerializer,
    MEISubmissionStatusSerializer,
)


class MEISubmissionView(generics.ListCreateAPIView):  # type: ignore[type-arg]
    """
    The deposit inbox for MEI produced by an external OMR pipeline.

    POST accepts one folio's MEI and files it for review. GET reports the status
    of one submitter's submissions, so the submitting system can show a user what
    became of their work.

    Authentication is a DRF token belonging to a service account for the
    submitting application, not to the person who did the OMR work -- the
    submitter's own username travels in the request body. Permissions are the
    model's: POST needs `cantusdata.add_meisubmission`, GET needs
    `cantusdata.view_meisubmission`, both grantable from the admin.

    Note that these are set explicitly because the project configures no
    DEFAULT_PERMISSION_CLASSES, so DRF's default is AllowAny; naming
    TokenAuthentication explicitly also keeps CSRF out of a server-to-server POST.
    """

    queryset = MEISubmission.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [DjangoModelPermissions]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "mei_deposit"

    def get_serializer_class(self) -> Type[BaseSerializer]:  # type: ignore[type-arg]
        if self.request.method == "POST":
            return MEISubmissionCreateSerializer
        return MEISubmissionStatusSerializer

    def get_queryset(self) -> QuerySet[MEISubmission]:
        queryset = MEISubmission.objects.all()
        submitter = self.request.query_params.get("submitter")
        if submitter:
            queryset = queryset.filter(submitter=submitter)
        return queryset

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # A resubmission of byte-identical content is the same request arriving
        # twice, not a second thing to review, so report the review that already
        # exists instead of creating another.
        duplicate = serializer.find_duplicate()  # type: ignore[union-attr]
        if duplicate is not None:
            return Response(
                MEISubmissionStatusSerializer(duplicate).data,
                status=status.HTTP_200_OK,
            )
        submission = serializer.save()
        return Response(
            MEISubmissionStatusSerializer(submission).data,
            status=status.HTTP_201_CREATED,
        )
