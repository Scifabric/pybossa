/*
 * jQuery scrollsync Plugin
 * version: 1.0 (30 -Jun-2009)
 * Copyright (c) 2009 Miquel Herrera
 *
 * Dual licensed under the MIT and GPL licenses:
 *   http://www.opensource.org/licenses/mit-license.php
 *   http://www.gnu.org/licenses/gpl.html
 *
 */
;(function($){ // secure $ jQuery alias

/**
 * Synchronizes scroll of one element (first matching targetSelector filter)
 * with all the rest meaning that the rest of elements scroll will follow the 
 * matched one.
 * 
 * options is composed of the following properties:
 *	------------------------------------------------------------------------
 *	targetSelector	| A jQuery selector applied to filter. The first element of
 *					| the resulting set will be the target all the rest scrolls
 *					| will be synchronised against. Defaults to ':first' which 
 *					| selects the first element in the set.
 *	------------------------------------------------------------------------
 *	axis			| sets the scroll axis which will be synchronised, can be
 *					| x, y or xy. Defaults to xy which will synchronise both.
 *	------------------------------------------------------------------------
 */
$.fn.scrollsync = function( options ){
	var settings = $.extend(
			{   
				targetSelector:':first',
				axis: 'xy'
			},options || {});
	
	
	function scrollHandler(event) {
		if (event.data.xaxis){
			event.data.followers.scrollLeft(event.data.target.scrollLeft());
		}
		if (event.data.yaxis){
			event.data.followers.scrollTop(event.data.target.scrollTop());
		}
	}
	
	// Find target to follow and separate from followers
	settings.target = this.filter(settings.targetSelector).filter(':first');
	settings.followers=this.not(settings.target); // the rest of elements

	// Parse axis
	settings.xaxis= (settings.axis=='xy' || settings.axis=='x') ? true : false; 
	settings.yaxis= (settings.axis=='xy' || settings.axis=='y') ? true : false;
	if (!settings.xaxis && !settings.yaxis) return;  // No axis left 
	
	// bind scroll event passing array of followers
	settings.target.bind('scroll', settings, scrollHandler);
	
}; // end plugin scrollsync

})( jQuery ); // confine scope
