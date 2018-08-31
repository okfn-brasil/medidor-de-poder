from collections import Counter
from unidecode import unidecode

from tqdm import tqdm

from perfil.person.models import Person
from perfil.utils.management.commands import ImportCsvCommand
from perfil.utils.infos import GENDERS
from perfil.utils.tools import (parse_date, probably_same_entity,
                                treat_birthday)


class Command(ImportCsvCommand):

    help = "Import CSV generated by: https://brasil.io/dataset/eleicoes-brasil/candidatos"  # noqa
    model = Person
    bulk_size = 2 ** 10
    slice_csv = False

    def group_names_by_cpf(self, reader, total):
        grouped = {}
        original_desc = f'Importing {self.model_name} data'
        desc = 'Cleaning data'.ljust(len(original_desc), ' ')
        with tqdm(total=total, desc=desc, unit='lines') as progress_bar:
            for line in reader:
                cpf, name = line['cpf_candidato'], line['nome_candidato']
                grouped_cpf = grouped.get(cpf, {})
                names = grouped_cpf.get('names', set())
                names.add(name)
                grouped[cpf] = {
                    'names': names,
                    'birthday': treat_birthday(line['data_nascimento']),
                    'voter_id': line['num_titulo_eleitoral_candidato'],
                    'gender': line['descricao_sexo'],
                    'birthplace_state': line['sigla_uf_nascimento'],
                    'birthplace_city': line['nome_municipio_nascimento'],
                }
                progress_bar.update(1)

        return grouped

    def serialize(self, reader, total, progress_bar):
        data = self.group_names_by_cpf(reader, total)
        progress_bar.update(total - len(data))

        for cpf, infos in data.items():
            names = infos['names']
            if len(names) == 1 or probably_same_entity(names):
                *_, name = names  # last should be the most recent one
                yield Person(
                    civil_name=unidecode(name),
                    cpf=cpf,
                    gender=GENDERS[infos['gender']],
                    voter_id=infos['voter_id'],
                    birthday=infos['birthday'],
                    birthdate=parse_date(infos['birthday']),
                    birthplace_city=infos['birthplace_city'],
                    birthplace_state=infos['birthplace_state'],
                )
            else:
                yield None
