"""Transactional project organization operations."""
import sqlalchemy as sa
from uuid import uuid4
from museforge.db import schema as db
from museforge.jobs import row, scoped


def duplicate(engine, settings, identifier):
    with engine.begin() as c:
        source = row(c, db.projects, identifier, settings, True)
        originals = c.execute(sa.select(db.versions).where(
            scoped(db.versions, settings), db.versions.c.project_id == identifier
        ).order_by(db.versions.c.number).with_for_update()).mappings().all()
        remap = {item['id']: uuid4() for item in originals}
        title = ('Copy of ' + source['title'])[:120]
        project = dict(c.execute(db.projects.insert().values(
            workspace_id=settings.workspace_id,
            title=title,
            draft=source['draft'],
            active_version_id=None,
            revision=1,
            selection_epoch=0,
            latest_submission_seq=0,
            next_version_number=max((item['number'] for item in originals), default=0) + 1,
        ).returning(db.projects)).mappings().one())
        for item in originals:
            version_id = remap[item['id']]
            c.execute(db.versions.insert().values(
                id=version_id,
                workspace_id=settings.workspace_id,
                project_id=project['id'],
                parent_version_id=remap.get(item['parent_version_id']),
                origin_version_id=item['id'],
                generation_job_id=None,
                number=item['number'],
                label=item['label'],
                revision=1,
                inputs=item['inputs'],
                lyrics=item['lyrics'],
                structure=item['structure'],
                provenance=item['provenance'],
                snapshot_schema_version=item['snapshot_schema_version'],
                audio_recomposed=item['audio_recomposed'],
            ))
            for link in c.execute(sa.select(db.links).where(db.links.c.version_id == item['id'])).mappings():
                c.execute(db.links.insert().values(
                    workspace_id=settings.workspace_id,
                    version_id=version_id,
                    artifact_id=link['artifact_id'],
                    role=link['role'],
                ))
        if source['active_version_id']:
            project = dict(c.execute(db.projects.update().where(db.projects.c.id == project['id']).values(
                active_version_id=remap[source['active_version_id']]
            ).returning(db.projects)).mappings().one())
    return project


def set_archived(connection, project, archived):
    if archived:
        active = connection.scalar(sa.select(sa.exists().where(
            db.jobs.c.project_id == project['id'],
            db.jobs.c.workspace_id == project['workspace_id'],
            db.jobs.c.state.not_in(('cancelled', 'succeeded', 'failed', 'timed_out')),
        )))
        if active:
            from museforge.domain import ProviderError
            raise ProviderError('active_jobs_conflict')
        return sa.func.now()
    return None
