#!/usr/bin/env zsh
#
# Run loto locally then push results upstream through a docker container.

# Run crawler.
cd ${LOTO_CRONJOB_REPOPATH}
source venv/bin/activate
/usr/bin/env python3 crawler.py
if [ $? != 0 ]; then
  echo 'crawler failed, quitting.'
  exit 1
fi
deactivate

# Upload results to container.
/usr/local/bin/docker start ${LOTO_CRONJOB_DOCKERID}
for f in $(ls -1 ${LOTO_CRONJOB_REPOPATH}/output/csv/*); do
  /usr/local/bin/docker cp ${f} ${LOTO_CRONJOB_DOCKERID}:/opt/loto/
done

# Upload upstream.
/usr/local/bin/docker exec ${LOTO_CRONJOB_DOCKERID} '/opt/push-upstream'
/usr/local/bin/docker stop ${LOTO_CRONJOB_DOCKERID}