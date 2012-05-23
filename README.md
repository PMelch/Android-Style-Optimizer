Android-Style-Optimizer
=======================

a tool that runs various optimization steps on a set of android style xml files.


Usage: asop.py [options] res_folder

Options:
  -h, --help            show this help message and exit
  -v, --verbose         if set, enables verbose output.
  -o OUTFOLDER, --outfolder=OUTFOLDER
                        if set, writes the generated files to the specified
                        out folder. if no folder is specified, no output is
                        generated.
                        
  res_folder: is the folder where there are the values[-xxxx] folders.

          
    the optimizer tries to handle sitations where you have the same style defined in different 
    xml files containing different size, color or integer values.
    
    example:
    
     in values-xlarge/styles.xml:
         <style name="sample_style">
             <item name="android:layout_width">100dp</item>
             <item name="android:layout_height">100dp</item>
         <style>
         
     in values-xhadpi/styles.xml
         <style name="sample_style">
             <item name="android:layout_width">200dp</item>
             <item name="android:layout_height">100dp</item>
         <style>
    
    
     the optimize process would create a styles.xml file in values containing:
         <style name="sample_style">
             <item name="android:layout_width">@dimen/SampleStyle_layoutWidth</item>
             <item name="android:layout_height">100dp</item>
         <style>
         
        and two styles.xml file in values-xlarge and values-xhdpi, resp.
        
        values-xlarge/styles.xml:
             <dimen name="SampleStyle_layoutWidth">100dp</dimen>
         
        values-xhdpi/styles.xml:
             <dimen name="SampleStyle_layoutWidth">200dp</dimen>
         
     
     
     Style declarations where one version has - say - a dimension as layout width, but the other
     version has "match_parent" cannot be merged, since a dimen item cannot hold the value "match_parent".
     
     Same goes for styles that have different items defined.
