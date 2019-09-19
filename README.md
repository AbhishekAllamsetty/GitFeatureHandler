# GitFeatureHandler
Selecting features what needs to be deployed after all the features has merged with develop branch

Usecase: When all the features are merged with the develop branch for deployement when in some case where we need to ignore some of the features from the develop branch (for which testing is not yet completed || not scheduled for production in the current release) those branches/features need to be excluded from merging into master for deployemnt would be a painful task in reverting the changes.
This helps to find the features which were not ready for deployement and would create a hotfix branch only with the required features.


Design Approach:
  --yet to update
