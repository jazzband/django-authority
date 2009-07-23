BEGIN;
-- Application: authority
-- Model: Permission
ALTER TABLE `authority_permission`
	ADD `date_requested` DATETIME;
ALTER TABLE `authority_permission`
	ADD `approved` BOOL;
ALTER TABLE `authority_permission`
	ADD `date_approved` DATETIME;
ALTER TABLE `authority_permission`
	MODIFY `object_id` INTEGER UNSIGNED;
UPDATE `authority_permission`
	SET `approved` = TRUE;
UPDATE `authority_permission`
	SET `date_approved` = NOW();
COMMIT;
