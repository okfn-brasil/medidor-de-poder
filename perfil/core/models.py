from datetime import date
from decimal import Decimal

from django.db import models
from django.db.models import JSONField
from django.contrib.postgres.fields import ArrayField

from perfil.core.managers import CampaignManager


STATES = (
    ("AC", "Acre"),
    ("AL", "Alagoas"),
    ("AP", "Amapá"),
    ("AM", "Amazonas"),
    ("BA", "Bahia"),
    ("CE", "Ceará"),
    ("DF", "Distrito Federal"),
    ("ES", "Espírito Santo"),
    ("GO", "Goiás"),
    ("MA", "Maranhão"),
    ("MT", "Mato Grosso"),
    ("MS", "Mato Grosso do Sul"),
    ("MG", "Minas Gerais"),
    ("PA", "Pará"),
    ("PB", "Paraíba"),
    ("PR", "Paraná"),
    ("PE", "Pernambuco"),
    ("PI", "Piauí"),
    ("RJ", "Rio de Janeiro"),
    ("RN", "Rio Grande do Norte"),
    ("RS", "Rio Grande do Sul"),
    ("RO", "Rondônia"),
    ("RR", "Roraima"),
    ("SC", "Santa Catarina"),
    ("SP", "São Paulo"),
    ("SE", "Sergipe"),
    ("TO", "Tocantins"),
)


def age(date_of_birth, election_year):
    """Calculates the age of the politician when they started in office"""
    reference = date(election_year + 1, 1, 1)
    correction_reference = correction = (reference.month, reference.day)
    correction_date_of_birth = (date_of_birth.month, date_of_birth.day)
    correction = correction_reference < correction_date_of_birth
    return reference.year - date_of_birth.year - correction


class City(models.Model):
    code = models.IntegerField()
    name = models.CharField(max_length=63, default="", blank=True)
    state = models.CharField(max_length=2, choices=STATES)

    def __repr__(self):
        return f"{self.name} - {self.state}"

    class Meta:
        verbose_name = "city"
        verbose_name_plural = "cities"
        ordering = ("name", "state")
        indexes = (models.Index(fields=("name", "state")),)


class Party(models.Model):
    name = models.CharField(max_length=63, default="", blank=True)
    abbreviation = models.CharField(max_length=15, default="", blank=True)

    class Meta:
        verbose_name = "party"
        verbose_name_plural = "parties"
        ordering = ("name",)
        indexes = (models.Index(fields=("abbreviation",)),)

    def __repr__(self):
        return self.abbreviation


class Affiliation(models.Model):
    """Store raw data about political party affiliations"""

    REGULAR = "R"
    CANCELED = "C"
    EXCLUDED = "D"
    SUB_JUDICE = "S"
    STATUSES = (
        (REGULAR, "Regular"),
        (CANCELED, "Cancelado"),
        (EXCLUDED, "Desfiliado"),
        (SUB_JUDICE, "Sub judice"),
    )

    name = models.CharField(max_length=127, default="", blank=True)
    voter_id = models.CharField(max_length=12, default="", blank=True)
    started_in = models.DateField()
    electoral_section = models.IntegerField()
    electoral_zone = models.IntegerField()
    party = models.ForeignKey(
        Party, on_delete=models.CASCADE, related_name="affiliated"
    )
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="affiliated")
    status = models.CharField(max_length=1, choices=STATUSES)
    ended_in = models.DateField(null=True)
    canceled_in = models.DateField(null=True)
    regularized_in = models.DateField(null=True)
    processed_in = models.DateField(null=True)
    extracted_in = models.DateTimeField(null=True)
    cancel_reason = models.CharField(max_length=31, default="", blank=True)

    def __repr__(self):
        return f"{self.name} ({self.party.abbreviation}/{self.city.state})"

    class Meta:
        verbose_name = "historical political affiliation"
        verbose_name_plural = "historical political affiliations"
        indexes = (
            models.Index(fields=("party",)),
            models.Index(fields=("name",)),
            models.Index(fields=("voter_id",)),
            models.Index(fields=("status",)),
            models.Index(fields=("started_in",)),
        )


class Politician(models.Model):
    """Subset of Affiliation keeping only the most recent and regular political
    party affiliation"""

    current_affiliation = models.OneToOneField(
        Affiliation, on_delete=models.CASCADE, related_name="politician"
    )
    affiliation_history = JSONField(default=list)
    asset_history = JSONField(default=list)
    election_history = JSONField(default=list)
    bill_keywords = JSONField(default=list)
    rosies_suspicions = JSONField(default=list)

    def __repr__(self):
        return (
            f"{self.current_affiliation.name} "
            f"({self.current_affiliation.party.abbreviation}"
            f"/{self.current_affiliation.city.state})"
        )

    class Meta:
        verbose_name = "politician"
        verbose_name_plural = "politicians"
        ordering = ("current_affiliation__name",)
        indexes = (models.Index(fields=("current_affiliation",)),)


class Candidate(models.Model):
    politician = models.ForeignKey(Politician, null=True, on_delete=models.CASCADE)
    voter_id = models.CharField(max_length=12, default="", blank=True)
    taxpayer_id = models.CharField(max_length=11, blank=True, default="")
    date_of_birth = models.DateField(null=True)
    place_of_birth = models.ForeignKey(City, null=True, on_delete=models.CASCADE)
    gender = models.CharField(max_length=16, blank=True, default="")
    email = models.CharField(max_length=128, blank=True, default="")
    age = models.CharField(max_length=16, blank=True, default="")

    ethnicity = models.CharField(max_length=16, blank=True, default="")
    ethnicity_code = models.CharField(max_length=2, blank=True, default="")
    marital_status = models.CharField(max_length=32, blank=True, default="")
    marital_status_code = models.CharField(max_length=32, blank=True, default="")
    education = models.CharField(max_length=32, blank=True, default="")
    education_code = models.CharField(max_length=16, blank=True, default="")
    nationality = models.CharField(max_length=64, blank=True, default="")
    nationality_code = models.CharField(max_length=32, blank=True, default="")
    occupation = models.CharField(max_length=128, blank=True, default="")
    occupation_code = models.CharField(max_length=64, blank=True, default="")

    election = models.CharField(max_length=64, blank=True, default="")
    year = models.IntegerField()
    state = models.CharField(max_length=2, choices=STATES)
    round = models.IntegerField()
    post = models.CharField(max_length=128, blank=True, default="")
    post_code = models.IntegerField()
    status = models.CharField(max_length=64, blank=True, default="")

    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, blank=True, default="")
    ballot_name = models.CharField(max_length=32, blank=True, default="")
    number = models.IntegerField(null=True)
    sequential = models.CharField(max_length=16, blank=True, default="")
    coalition_name = models.CharField(max_length=128, blank=True, default="")
    coalition_description = models.CharField(max_length=256, blank=True, default="")
    coalition_short_name = models.CharField(max_length=16, blank=True, default="")
    max_budget = models.CharField(max_length=16, blank=True, default="")

    round_result = models.CharField(max_length=64, blank=True, default="")
    round_result_code = models.IntegerField(null=True)

    objects = CampaignManager()

    def _history(self, prefix, sort_by="year"):
        if not self.politician:
            return []

        data = getattr(self.politician, f"{prefix}_history", [])
        return sorted(data, key=lambda obj: obj[sort_by])

    def affiliation_history(self):
        return self._history("affiliation", "started_in")

    def asset_history(self):
        return self._history("asset")

    def election_history(self):
        return self._history("election")

    def elections(self):
        return len(self.election_history())

    def elections_won(self):
        return sum(1 for election in self.election_history() if election["elected"])

    def bills(self):
        if not self.politician:
            return []

        return self.politician.bills.all()

    def bill_keywords(self):
        if not self.politician:
            return []

        data = self.politician.bill_keywords
        return sorted(data, key=lambda obj: obj["total"], reverse=True)

    def rosies_suspicions(self):
        return self.politician.rosies_suspicions if self.politician else []

    def image(self):
        if self.year != 2018:
            return None

        # TODO bucket configuration as a setting
        bucket = "https://serenata-de-amor-data.nyc3.digitaloceanspaces.com/"
        return f"{bucket}perfil-politico/{self.state}/{self.sequential}.jpg"

    def get_age(self):
        """The age column is blank too many times, so let's calculate it"""
        if self.age:
            return self.age

        if not self.date_of_birth:
            return None

        return age(self.date_of_birth, self.year)

    def __repr__(self):
        return f"{self.ballot_name} ({self.party.abbreviation}/{self.state})"

    class Meta:
        verbose_name = "candidate"
        verbose_name_plural = "candidates"
        ordering = ("-year", "ballot_name")
        indexes = (
            models.Index(fields=("politician",)),
            models.Index(fields=("voter_id",)),
            models.Index(fields=("year",)),
            models.Index(fields=("year", "state", "post", "ballot_name")),
            models.Index(fields=("round_result",)),
            models.Index(fields=("sequential",)),
        )


class Asset(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=16, decimal_places=2, null=True)
    category = models.CharField(max_length=128, blank=True, default="")
    category_code = models.IntegerField(null=True)
    detail = models.CharField(max_length=255, blank=True, default="")
    order = models.IntegerField(null=True)
    last_update = models.DateTimeField(null=True)

    def __repr__(self):
        return f"{self.category} (R$ {Decimal(self.value):,})"

    class Meta:
        verbose_name = "asset"
        verbose_name_plural = "assets"
        ordering = ("candidate__ballot_name", "-value")
        indexes = (models.Index(fields=("candidate",)), models.Index(fields=("value",)))


class Bill(models.Model):
    authors = models.ManyToManyField(Politician, related_name="bills")
    summary = models.TextField(blank=True, default="")
    name = models.CharField(max_length=16, blank=True, default="")
    keywords = ArrayField(models.CharField(max_length=255))
    source_id = models.IntegerField()
    url = models.URLField(unique=True)

    def __repr__(self):
        return self.name

    class Meta:
        verbose_name = "bill"
        verbose_name_plural = "bills"
        ordering = ("name",)
        indexes = (models.Index(fields=("keywords",)), models.Index(fields=("url",)))
