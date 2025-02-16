#!/bin/sh
echo "${SFTP_USER}:${SFTP_PASS}" | chpasswd
mkdir -p /home/${SFTP_USER}/uploads
chown ${SFTP_USER}:${SFTP_USER} /home/${SFTP_USER}/uploads
