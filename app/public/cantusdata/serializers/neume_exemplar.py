from typing import cast

from rest_framework import serializers
from django.db.models.query import QuerySet
from cantusdata.models import NeumeExemplar, Folio


class NeumeExemplarListSerializer(serializers.ListSerializer[NeumeExemplar]):
    def update(  # type: ignore
        self,
        instance: QuerySet[NeumeExemplar],
        validated_data: list[dict[str, str | int]],
    ) -> QuerySet[NeumeExemplar]:
        instance_mapping = {
            neume_exemplar.name: neume_exemplar for neume_exemplar in instance
        }
        for data in validated_data:
            # We know the value of the "name" key is a string
            neume_name = cast(str, data["name"])
            neume_exemplar = instance_mapping.get(neume_name, None)
            if neume_exemplar is not None:
                self.child.update(neume_exemplar, data)  # type: ignore[union-attr]

        return instance.all()


class NeumeExemplarSerializer(serializers.ModelSerializer[NeumeExemplar]):
    class Meta:
        model = NeumeExemplar
        fields = ["manuscript", "folio", "name", "p", "x", "y", "w", "h"]
        list_serializer_class = NeumeExemplarListSerializer

    manuscript: str = serializers.StringRelatedField(source="folio.manuscript.name")  # type: ignore
    folio: str = serializers.StringRelatedField(source="folio.number")  # type: ignore
    # These short forms match the values given in the boxes
    # in Solr OMR results
    p = serializers.SlugRelatedField(
        slug_field="image_uri",
        queryset=Folio.objects.all(),
        source="folio",
        style={"base_template": "input.html"},
    )
    x = serializers.IntegerField(source="x_coord")
    y = serializers.IntegerField(source="y_coord")
    w = serializers.IntegerField(source="width")
    h = serializers.IntegerField(source="height")
