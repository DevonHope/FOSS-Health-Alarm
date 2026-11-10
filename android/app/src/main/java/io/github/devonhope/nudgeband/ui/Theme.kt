package io.github.devonhope.nudgeband.ui

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

/** Colours for the sleep chart, the same in light and dark themes. */
object StageColors {
    val deep = Color(0xFF3F51B5)
    val light = Color(0xFF7FA7FF)
    val awake = Color(0xFFF4B860)
    val noData = Color(0x33888888)
    val wake = Color(0xFFE57373)
}

private val NightDark = darkColorScheme(
    primary = Color(0xFF9FB4FF),
    secondary = Color(0xFFF4D58D),
    background = Color(0xFF14182B),
    surface = Color(0xFF14182B),
    surfaceVariant = Color(0xFF242A47),
)

private val NightLight = lightColorScheme(
    primary = Color(0xFF3F51B5),
    secondary = Color(0xFF8A6D1F),
)

@Composable
fun NudgeTheme(content: @Composable () -> Unit) {
    val dark = isSystemInDarkTheme()
    val context = LocalContext.current
    val scheme = when {
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S ->
            if (dark) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        dark -> NightDark
        else -> NightLight
    }
    MaterialTheme(colorScheme = scheme, content = content)
}
