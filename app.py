import datetime
import json
import random

from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from sqlalchemy.orm import relationship

date_format = '%Y-%m-%d %H:%M:%S'


def seed_data(spaces=1, door_ways=1, person_enters_per_door=4, person_leaves_per_door=1):
    """
    Create a Space with doorways, counts for people entering and leaving.
    Default creates:
     1 Space
     1 Doorways
        For each Doorway:
            4 people entering 1 minute ago
            1 person leaving 2 minutes ago


    :param spaces:
    :param door_ways:
    :param person_enters_per_door:
    :param person_leaves_per_door:
    :param days_time_delta:
    :return:
    """
    # Create space(s)
    for i in range(0, spaces):
        space = Space()
        installations = []
        # Create doorway(s)
        for k in range(0, door_ways):
            dpu = Dpu()
            installation = Installation(dpu=dpu)

            installations.append(installation)
            doorway = Doorway(installation_id=installation.id)
            db.session.add(doorway)
            db.session.commit()
            installation.doorway_id = doorway.id

            db.session.add(installation)
            space.doorways.append(doorway)
            db.session.commit()

            doorway.installation_id = installation.id
            db.session.commit()

            # Create +1s
            for j in range(0, person_enters_per_door):
                plus_1_installation_count = InstallationCount(
                    installation_id=installation.id,
                    count=1,
                    dpu_event_time=datetime.datetime.utcnow() + datetime.timedelta(minutes=-2)
                )
                db.session.add(plus_1_installation_count)

            # Create -1s
            time_left = None
            for l in range(0, person_leaves_per_door):
                minus_1_installation_count = InstallationCount(
                    installation_id=installation.id,
                    count=-1,
                    dpu_event_time=datetime.datetime.utcnow() + datetime.timedelta(minutes=-1)
                )
                time_left = minus_1_installation_count.dpu_event_time.strftime(date_format)
                db.session.add(minus_1_installation_count)
        db.session.add(space)
    db.session.commit()
    print(f'Created Space with id: {space.id}')
    print(f'A GET to \'http://127.0.0.1:5000/spaces/{space.id}\' should return a count of 3')
    print(f'A GET to \'http://127.0.0.1:5000/spaces/{space.id}?time={time_left}\' should return a count of 4')


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\Work\Fun\density-api\dbdensity.db'
db = SQLAlchemy(app)


class Serializer(object):

    # https://stackoverflow.com/questions/7102754/jsonify-a-sqlalchemy-result-set-in-flask
    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]


# --------------- DB Models --------------------------------------------------------


class Space(db.Model, Serializer):
    id = db.Column(db.Integer, primary_key=True)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    doorways = relationship("Doorway", lazy='dynamic')

    def serialize(self):
        d = Serializer.serialize(self)
        d['created_date'] = str(d['created_date'])
        return d


class Doorway(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    space_id = db.Column(db.Integer, db.ForeignKey('space.id'))
    installation_id = db.Column(db.Integer, db.ForeignKey('installation.id'))


class Dpu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    installation = relationship("Installation", back_populates="dpu")


# TODO - Restrict a Doorway to only have one "active" Installation at a time.
# Assumption - Only one DPU can be installed on a given Doorway.
class Installation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_date = db.Column(db.DateTime)
    doorway_id = db.Column(db.Integer, db.ForeignKey('doorway.id'))
    dpu_id = db.Column(db.Integer, db.ForeignKey('dpu.id'))
    dpu = relationship("Dpu", back_populates="installation")
    installation_count = relationship("InstallationCount")


class InstallationCount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    dpu_event_time = db.Column(db.DateTime)
    installation_id = db.Column(db.Integer, db.ForeignKey('installation.id'))
    installation = relationship("Installation", back_populates="installation_count")
    count = db.Column(db.Integer)


# -------------------------- End DB Models ------------------------------------------------


db.create_all()

# Use this to seed all the data
seed_data()

@app.route('/stats')
def get_stats():
    # Use this to make sure you have seeded data into with seed_data()
    stats = {}
    stats['spaces'] = f'{len(Space.query.all())}'
    stats['doorways'] = f'{len(Doorway.query.all())}'
    stats['dpus'] = f'{len(Dpu.query.all())}'
    stats['installations'] = f'{len(Installation.query.all())}'
    stats['installation_counts'] = f'{len(InstallationCount.query.all())}'
    return json.dumps(stats)


@app.route('/spaces/<id>', methods=['GET'])
def spaces_info(id):
    # Get query params
    time = request.args.get('time')

    try:
        results = process_space_query(space_id=id, time=time)
        return json.dumps(results)
    except Exception as ex:
        return abort(500)


def process_space_query(space_id, time):
    """
    Encapsulated business logic for handling count queries.
    TODO - Move into something like space_manager.py
    :param space_id:
    :param time:
    :return Space info:
    """
    space_time_str = ''
    count = 0
    results = {}


    search_dt_add_one_minute = None
    search_dt_subtract_one_minute = None
    if time is not None:
        search_dt = datetime.datetime.strptime(time, date_format)
        space_time_str = search_dt.strftime(date_format)
        search_dt_add_one_minute = (search_dt + datetime.timedelta(minutes=1)).strftime(date_format)
        search_dt_subtract_one_minute = (search_dt + datetime.timedelta(minutes=-1)).strftime(date_format)
    else:
        now_utc = datetime.datetime.utcnow()
        space_time_str = now_utc.strftime(date_format)
        search_dt_add_one_minute = (now_utc + datetime.timedelta(minutes=1)).strftime(date_format)
        search_dt_subtract_one_minute = (now_utc + datetime.timedelta(minutes=-1)).strftime(date_format)

    # TODO - Use ORM to query DB.
    # TODO - In Prod, look into memory and/or Redis before looking in the DB for optimal queries.
    # TODO - Validate inputs to protect against SQL injection.
    sql = 'select sum(ic.count) ' \
          'from Space s ' \
          'join doorway d on s.id = d.space_id ' \
          'join installation i on d.id = i.doorway_id ' \
          'join installation_count ic on i.id = ic.installation_id ' \
          f'where s.id = {space_id} ' \
          f'and ic.dpu_event_time <= \'{space_time_str}\' '
    print(f'sql: {sql}')
    result = db.engine.execute(sql)
    db_count_result = [row[0] for row in result][0]
    if db_count_result is not None:
        count = db_count_result
    results['id'] = space_id
    results['count'] = count
    results['time'] = space_time_str
    return results


if __name__ == '__main__':
    app.run()
