import csv
import pandas
import os

def reorg_cohort_files(region, projection, years, state_numbers, area_threshold):

    path_to_data = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}' .format(region)

    state_codes = pandas.read_csv('C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/state_numbers.csv', dtype={'Number': str})

    for year in years:

        csv_filename_results = path_to_data + '/cohort_municipalities_nowetlands_{0}_{1}percent_{2}_{3}_all_states.csv' .format(region, area_threshold, year, projection)

        with open(csv_filename_results, 'ab') as csvfile:

            for state_number in state_numbers:

                file_to_check = path_to_data + '/cohort_municipalities_nowetlands_by_year_{0}_{1}percent_{2}_state{3}.csv'.format(region, area_threshold, projection, state_number)

                if os.stat(file_to_check).st_size == 0:

                    print 'No inundated municipalities'

                else:

                    file_to_read = pandas.read_csv(file_to_check, header=None)

                    for index, row in state_codes.iterrows():

                        #print row[0]

                        if str(row[0]) == state_number:
                            state_abbr = row[1]

                    for index, row in file_to_read.iterrows():

                        #print row[0]

                        if str(row[0]) == year:

                            if row[2] == 'County subdivisions not defined':
                                print 'skipping'

                            else:

                                writer = csv.writer(csvfile)

                                writer.writerow([state_abbr, row[0], row[1],row[2], row[3]])

        print 'wrote file for year ' + year



#reorg_cohort_files('east_coast','NCAH',['2006','2100'],['01','09','10'],'10')
#reorg_cohort_files('east_coast','NCAH',['2006','2030','2045','2060','2070','2080','2090','2100'],['01','09','10','11','12','13','22','23','24','25','28','33','34','36','37','42','44','45','48','51'], '10')

# reorg_cohort_files('east_coast','NCAH',['2006','2030','2045','2060','2070','2080','2090','2100'],['01','09','10','11','12','13','22','23','24','25','28','33','34','36','37','42','44','45','48','51'], '10')
#
# reorg_cohort_files('west_coast','NCAH',['2006','2030','2045','2060','2070','2080','2090','2100'],['06','41','53'], '10')
#
# reorg_cohort_files('east_coast','NCAI',['2035','2060','2080','2100'],['01','09','10','11','12','13','22','23','24','25','28','33','34','36','37','42','44','45','48','51'], '10')
#
# reorg_cohort_files('west_coast','NCAI',['2035','2060','2080','2100'],['06','41','53'], '10')






